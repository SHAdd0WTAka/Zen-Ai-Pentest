# Security Testing Modules - Dokumentation

> ⚠️ **WARNUNG: DIESER ORDNER ENTHÄLT TATSÄCHLICHEN EXPLOIT-CODE**  
> Diese Module enthalten FUNktionierenden Code für Sicherheitsangriffe.  
> Missbrauch ist **STRAFBAR**!

---

## ⚠️ Ehrliche Aufklärung (Wir verschönieren nichts!)

### Was ist hier wirklich enthalten?

Diese Dateien enthalten **tatsächlichen Exploit-Code**, der für reale Angriffe verwendet werden kann:

| Datei | Was sie wirklich tut |
|-------|---------------------|
| `test_dast.py` | Enthält Payloads für SQL Injection, XSS, Command Injection |
| `lfi_rfi_module.py` | Enthält Web-Shell-Code und Datei-Inclusion-Techniken |
| `recommended_security_modules.py` | Enthält Exploit-Payloads für verschiedene Angriffsvektoren |

### Warum Anti-Virus Alarm schlägt

**Der Alarm ist BERECHTIGT!** Diese Dateien enthalten:
- PHP-Code zur Code-Ausführung (`system()`, `exec()`)
- Techniken zur Rechteausweitung
- Methoden zur Datenexfiltration
- Exploit-Payloads

Dies ist **kein typischer False Positive** - die Dateien enthalten tatsächlich Werkzeuge, die für Angriffe verwendet werden können.

---

## 📁 Module

### 1. DAST Tests (`test_dast.py`)
**Standort:** `tests/security/test_dast.py`

**Was es enthält:**
- SQL-Injection Test-Payloads (`' OR '1'='1`, `UNION SELECT`)
- Command Injection Payloads (`; cat /etc/passwd`, `| whoami`)
- XSS-Payloads (`<script>alert(1)</script>`)
- Web-Shell-Testdateien (`.php`, `.jsp`, `.asp`)

**Risiko:**
- Enthält Code-Snippets, die kopiert und für Angriffe verwendet werden können
- Test-Payloads können in falschen Händen Schaden anrichten

**Verwendung:**
```bash
cd tests/security
pytest test_dast.py -v
```

---

### 2. LFI/RFI Modul (`lfi_rfi_module.py`)
**Standort:** `modules/exploits/lfi_rfi_module.py`

**Was es enthält:**
- PHP Web-Shells (`<?php system($_GET['cmd']); ?>`)
- LFI-Techniken zum Auslesen von Systemdateien
- RFI-Methoden für Remote Code Execution
- PHP-Wrapper für Datei-Inclusion

**Risiko:**
- **HOCH** - Enthält funktionierenden Web-Shell-Code
- Kann direkt für Angriffe verwendet werden
- Ermöglicht Server-Kompromittierung

**Ausführungsmodi:**
- `SIMULATION` - Zeigt Payloads an, führt keine Angriffe aus
- `SAFE` - Führt lesende Operationen aus (kann trotzdem Daten preisgeben!)
- `FULL` - Nicht implementiert (Sicherheitsgründe)

---

### 3. Recommended Security Modules (`recommended_security_modules.py`)
**Standort:** `modules/recommended_security_modules.py`

**Was es enthält:**
- CSRF-Testmethoden
- SSRF-Payloads für interne Netzwerk-Zugriffe
- Path Traversal Payloads (`../../../etc/passwd`)
- XSS-Payloads für verschiedene Kontexte
- Test-Dateien für bösartige Uploads

**Risiko:**
- **MITTEL** - Enthält Exploit-Techniken und Payloads
- Payloads können für Angriffe verwendet werden

---

## ⚖️ Legal Framework

### Was ist erlaubt?

| Szenario | Erlaubt? | Bedingungen |
|----------|----------|-------------|
| Eigene Systeme testen | ✅ Ja | Sie müssen Eigentümer sein |
| Autorisierte Pentests | ✅ Ja | Schriftliche Genehmigung nötig |
| CTF-Wettbewerbe | ✅ Ja | Innerhalb der Regeln |
| Sicherheitsforschung | ✅ Ja | In isolierten Labs |
| Bug Bounty | ✅ Ja | Innerhalb des definierten Scopes |

### Was ist ILLEGAL?

| Szenario | Illegal? | Konsequenzen |
|----------|----------|--------------|
| Fremde Systeme ohne Erlaubnis | ❌ Ja | Haftstrafe, Geldstrafe |
| Produktivsysteme testen | ❌ Ja | Zivilrechtliche Klage |
| Daten abgreifen | ❌ Ja | Datenschutzverletzung |
| Verfügbarkeit beeinträchtigen | ❌ Ja | Sabotage |

---

## 🛡️ Sicherheitsmaßnahmen

### 1. Isolierte Umgebung

```powershell
# Empfohlene Setup:
# 1. Virtuelle Maschine (VM)
# 2. Keine Netzwerkverbindung zum Produktivnetz
# 3. Snapshots vor Tests
# 4. Verschlüsselte Festplatte
```

### 2. Keine Speicherung auf Produktivsystemen

**NICHT TUN:**
- ❌ Auf Firmen-Laptops speichern
- ❌ Auf Produktivservern ausführen
- ❌ In Cloud-Speichern ohne Verschlüsselung

### 3. Anti-Virus Handling

**Option A: Ausschlüsse (nur für isolierte Systeme)**
```powershell
Add-MpPreference -ExclusionPath "C:\pentest\zen-ai-pentest"
```

**Option B: Docker-Container (empfohlen)**
```bash
docker-compose up -d
docker exec -it zen-ai-pentest bash
```

**Option C: Kali Linux VM (empfohlen)**
- Dedizierte Pentest-VM
- Regelmäßige Snapshots
- Keine Verbindung zu Produktivsystemen

---

## 📋 Verantwortungsvolle Offenlegung

Wenn Sie Schwachstellen finden:

1. **DOKUMENTIEREN** - Screenshots, Logs, Reproduktionsschritte
2. **NICHT AUSNUTZEN** - Keine Daten extrahieren
3. **MELDEN** - Kontaktieren Sie den Systemeigentümer
4. **WARTEN** - Geben Sie Zeit für Patches (90 Tage Standard)
5. **VERÖFFENTLICHUNG** - Nur nach Behebung oder mit Erlaubnis

---

## 🔍 Realistische Risikobewertung

### Wer sollte diesen Code verwenden?

✅ **Geeignet für:**
- Professionelle Penetrationstester
- Sicherheitsforscher
- CTF-Spieler
- Security-Administratoren (für eigene Systeme)

❌ **NICHT geeignet für:**
- Neugierige Anfänger ohne mentoren
- Menschen, die "nur mal testen" wollen
- Jemanden ohne Verständnis der rechtlichen Konsequenzen

---

## 📞 Support & Kontakt

Bei Fragen zur Legalität:
- EFF (Electronic Frontier Foundation): https://www.eff.org/
- OWASP Legal Project: https://owasp.org/

Bei technischen Fragen:
- GitHub Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues

---

## 📝 Haftungsausschluss (Auf Deutsch)

```
DIE SOFTWARE WIRD "WIE BESEHEN" BEREITGESTELLT, OHNE JEGLICHE GEWÄHRLEISTUNG, 
AUSDRÜCKLICH ODER STILLSCHWEIGEND, EINSCHLIESSLICH, ABER NICHT BESCHRÄNKT AUF 
DIE GEWÄHRLEISTUNG DER MARKTGÄNGIGKEIT, DER EIGNUNG FÜR EINEN BESTIMMTEN ZWECK 
UND DER NICHTVERLETZUNG VON RECHTEN. IN KEINEM FALL SIND DIE AUTOREN ODER 
COPYRIGHT-INHABER FÜR JEGLICHE ANSPRÜCHE, SCHÄDEN ODER SONSTIGE HAFTUNGEN 
VERANTWORTLICH, SEI ES DURCH VERTRAG, UNERLAUBTE HANDLUNG ODER ANDERWEITIG, 
DIE SICH AUS DER SOFTWARE ODER DER VERWENDUNG DER SOFTWARE ERGEBEN.

DER BENUTZER TRÄGT DIE ALLEINVERANTWORTUNG FÜR DIE VERWENDUNG DIESER SOFTWARE.
```

---

**Letzte Aktualisierung:** 14.02.2026  
**Version:** 1.0.0 - "Ehrliche Aufklärung Edition"  
**Autor:** Zen-AI-Pentest Team

> *"Wir verschönieren nichts. Dies ist mächtiger Code - verwendet ihn verantwortungsvoll."*
