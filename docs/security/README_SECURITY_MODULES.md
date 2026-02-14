# Security Testing Modules - Documentation

> ⚠️ **IMPORTANT LEGAL NOTICE**  
> Diese Module sind für **autorisierte Sicherheitstests** und **Bildungszwecke** bestimmt.  
> Unautorisierte Verwendung ist **ILLEGAL**. Der Autor übernimmt keine Haftung für Missbrauch.

---

## Übersicht

Dieses Verzeichnis enthält Sicherheitsmodule für das Zen-AI-Pentest Framework. Diese Module implementieren Tests für gängige Webanwendungsschwachstellen basierend auf der [OWASP Top 10](https://owasp.org/www-project-top-ten/).

## Module

### 1. DAST Tests (`test_dast.py`)
**Standort:** `tests/security/test_dast.py`

Dynamische Anwendungssicherheitstests (Dynamic Application Security Testing) für die Zen-AI-Pentest API.

**Testabdeckung:**
- Authentifizierungssicherheit (Brute-Force, Session Fixation)
- Injection-Angriffe (SQL, NoSQL, Command, XSS)
- Zugriffskontrolle (IDOR, Privilege Escalation)
- Security Headers (HSTS, CSP, X-Frame-Options)
- CSRF-Schutz
- Rate Limiting
- SSRF-Prävention
- Datei-Upload Sicherheit

**Verwendung:**
```bash
cd tests/security
pytest test_dast.py -v
```

---

### 2. LFI/RFI Modul (`lfi_rfi_module.py`)
**Standort:** `modules/exploits/lfi_rfi_module.py`

Exploit-Modul für Local/Remote File Inclusion Schwachstellen.

**Funktionen:**
- PHP-Wrapper Tests (php://filter, php://input, data://)
- LFI-Datei-Lesetests
- RFI-URL-Validierung
- Base64-Filter Dekodierung

**Ausführungsmodi:**
- `SIMULATION` - Keine tatsächlichen Angriffe (empfohlen)
- `SAFE` - Nur lesende Operationen
- `FULL` - Nicht implementiert (Sicherheitsgründe)

**Verwendung:**
```python
from modules.exploits.lfi_rfi_module import LFIRFIModule

module = LFIRFIModule()
# Siehe Modul-Dokumentation für Details
```

---

### 3. Recommended Security Modules (`recommended_security_modules.py`)
**Standort:** `modules/recommended_security_modules.py`

Sammlung von Sicherheitsscannern nach OWASP Top 10.

**Module:**
1. **CSRFScanner** - Cross-Site Request Forgery Detection
2. **SSRFScanner** - Server-Side Request Forgery Detection
3. **AccessControlScanner** - IDOR & Path Traversal
4. **AuthenticationTester** - Brute Force & Password Policy
5. **SessionManager** - Session Security
6. **XSSScannerEnhanced** - Cross-Site Scripting Detection
7. **APISecurityScanner** - REST/GraphQL API Testing
8. **FileUploadTester** - Malicious File Upload Detection

---

## Anti-Virus Hinweis

### Warum werden diese Dateien erkannt?

Diese Dateien enthalten **Test-Payloads** für Sicherheitstests, die von einigen Anti-Virus Programmen als verdächtig kennzeichnet werden:

- **PHP-Shell-Code** (in Test-Payloads)
- **SQL-Injection Patterns**
- **XSS-Payloads**
- **Path Traversal Strings**

**Dies ist ein FALSE POSITIVE!**

Die Payloads sind notwendig, um zu testen, ob Anwendungen diese Angriffe korrekt blockieren.

### Empfohlene Lösungen

#### Option 1: Windows Defender Ausschlüsse (Empfohlen)
```powershell
# Als Administrator ausführen
Add-MpPreference -ExclusionPath "C:\Users\Ataka\zen-ai-pentest"
Add-MpPreference -ExclusionPath "C:\Users\Ataka\zen-ai-pentest\tests\security"
Add-MpPreference -ExclusionPath "C:\Users\Ataka\zen-ai-pentest\modules\exploits"
```

#### Option 2: Docker-Verwendung
```bash
docker-compose up -d
# Alle Tests laufen isoliert im Container
```

#### Option 3: Isolierte VM
- Verwenden Sie eine separate Virtual Machine für Pentesting
- Snapshots vor Tests erstellen

---

## Sicherheitsrichtlinien

### Erlaubte Verwendung ✅
- Autorisierte Penetrationstests mit schriftlicher Erlaubnis
- Sicherheitsbewertungen eigener Systeme
- Sicherheitsforschung in isolierten Testumgebungen
- Bildungszwecke in kontrollierten Lernumgebungen
- Bug Bounty Programme (mit Erlaubnis)

### Verbotene Verwendung ❌
- Unautorisierte Zugriffe auf fremde Systeme
- Datenbeschaffung ohne Einwilligung
- Aktivitäten, die Datenschutzverletzungen verursachen
- Denial-of-Service Angriffe ohne Genehmigung
- Jegliche illegalen Aktivitäten

---

## Verantwortungsvolle Offenlegung

Wenn Sie Schwachstellen finden:

1. **Nicht ausnutzen** - Melden Sie sie verantwortungsvoll
2. **Dokumentieren** - Sammeln Sie Beweise
3. **Meldung** - Kontaktieren Sie den Systemeigentümer
4. **Wartezeit** - Geben Sie Zeit für Patches (typisch 90 Tage)
5. **Veröffentlichung** - Nur nach Behebung oder mit Erlaubnis

---

## Haftungsausschluss

```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Lizenz

Diese Module sind Teil des Zen-AI-Pentest Frameworks und unterliegen der MIT-Lizenz.

---

## Support

Bei Fragen oder Problemen:
- GitHub Issues: https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
- Dokumentation: Siehe `docs/` Verzeichnis

---

**Letzte Aktualisierung:** 14.02.2026  
**Version:** 1.0.0  
**Autor:** Zen-AI-Pentest Team
