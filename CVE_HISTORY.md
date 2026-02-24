# CVE History & Security Changelog

Chronologische Übersicht aller behobenen Sicherheitslücken.

## 2026-02-24 - Security Hardening Sprint

### CVE-2024-21503 (ReDoS in black)

**Severity:** Medium
**CVSS Score:** 5.3 (MEDIUM)
**Package:** black < 24.3.0
**Fixed in:** black 26.1.0

**Beschreibung:**
Die Funktion `lines_with_leading_tabs_expanded()` in `strings.py` war anfällig für Regular Expression Denial of Service (ReDoS). Ein Angreifer konnte durch speziell crafted Input mit tausenden von führenden Tab-Zeichen in Docstrings eine Denial of Service verursachen.

**Angriffsvektor:**
- Lokale Ausführung von Black auf untrusted Input
- Sehr lange Verarbeitungszeiten durch ineffiziente Regex

**Fix:**
Upgrade auf black >= 24.3.0 (wir haben 26.1.0 installiert)

**Impact für Zen-AI-Pentest:**
- Gering, da Black nur in Entwicklung verwendet wird
- Keine Production-Auswirkung

---

### CVE-2024-23342 (Minerva Timing Attack in python-ecdsa)

**Severity:** Medium
**CVSS Score:** 5.9 (MEDIUM)
**Package:** ecdsa <= 0.19.1
**Fixed by:** Migration zu PyJWT 2.11.0

**Beschreibung:**
Die `python-ecdsa` Bibliothek war anfällig für Minerva Timing Attacks auf der P-256 Kurve. Durch das Timing von Signaturen konnte ein Angreifer den internen Nonce leaken, was zur Berechnung des Private Keys führen könnte.

**Betroffen:**
- ECDSA Signatur-Erstellung
- Key Generation
- ECDH Operationen

**Nicht betroffen:**
- ECDSA Signatur-Verifikation

**Angriffsvektor:**
- Seitenkanal-Angriff (Side-Channel)
- Präzise Zeitmessung der Signatur-Operationen erforderlich
- Lokaler Zugriff oder sehr präzise Netzwerk-Timing

**Warum kein Patch verfügbar war:**
Das python-ecdsa Projekt betrachtet Side-Channel Angriffe als "out of scope" und hat keinen Fix geplant.

**Unsere Lösung:**
Migration von `python-jose` (verwendet ecdsa) zu `PyJWT` 2.11.0
- PyJWT verwendet cryptography Bibliothek (sicher)
- Cryptography ist constant-time implementiert
- Aktiv maintained

**Impact für Zen-AI-Pentest:**
- Hoch, da JWT-Authentifizierung verwendet wird
- Durch Migration zu PyJWT vollständig behoben

---

### PYSEC-2022-42969 (ReDoS in py)

**Severity:** Low
**CVSS Score:** 3.7 (LOW)
**Package:** py <= 1.11.0
**Fixed by:** Migration zu tenacity 9.1.4

**Beschreibung:**
Die `py` Bibliothek ermöglichte einen Regular Expression Denial of Service (ReDoS) Angriff durch manipulierte Subversion Repository Info-Daten. Die `InfoSvnCommand` verarbeitete bestimmte Regex-Muster ineffizient.

**Angriffsvektor:**
- Verarbeitung von Subversion Repositories
- Speziell crafted SVN metadata

**Warum kein Patch verfügbar war:**
Die `py` Bibliothek wird nicht mehr aktiv maintained. Das letzte Release war 1.11.0 (2022).

**Unsere Lösung:**
- Entfernung von `retry` (verwendet py)
- Migration zu `tenacity` 9.1.4 (modern, maintained)
- Entfernung des orphaned `py` Pakets

**Impact für Zen-AI-Pentest:**
- Niedrig, da nur in Dev-Dependencies verwendet
- Keine Production-Auswirkung

---

## Security Improvements Summary

### Vor dem Fix (2026-02-24)
```
4 Vulnerabilities found:
- black 24.1.1 (CVE-2024-21503) [MEDIUM]
- ecdsa 0.19.1 (CVE-2024-23342) [MEDIUM]
- py 1.11.0 (PYSEC-2022-42969) [LOW]
```

### Nach dem Fix (2026-02-24)
```
✅ No known vulnerabilities found
- black 26.1.0 (fixed)
- PyJWT 2.11.0 (replaced python-jose/ecdsa)
- tenacity 9.1.4 (replaced retry/py)
```

### Dependency Replacements

| Altes Paket | CVE | Neues Paket | Grund |
|-------------|-----|-------------|-------|
| python-jose 3.5.0 | CVE-2024-23342 | **PyJWT 2.11.0** | Sicher, maintained |
| ecdsa 0.19.1 | CVE-2024-23342 | *entfernt* | Inaktiv seit 2024 |
| retry 0.9.2 | PYSEC-2022-42969 | **tenacity 9.1.4** | Sicher, maintained |
| py 1.11.0 | PYSEC-2022-42969 | *entfernt* | Inaktiv seit 2022 |

---

## Chronologie

```
2026-02-24 09:30 - CVE-2024-21503 identifiziert (black)
2026-02-24 09:35 - CVE-2024-23342 identifiziert (ecdsa)
2026-02-24 09:35 - PYSEC-2022-42969 identifiziert (py)
2026-02-24 09:40 - Fix: black upgrade zu 26.1.0
2026-02-24 09:45 - Fix: Migration python-jose → PyJWT
2026-02-24 09:50 - Fix: Migration retry → tenacity
2026-02-24 09:55 - Cleanup: Entfernung orphaned dependencies
2026-02-24 10:00 - Verifikation: 0 vulnerabilities found
2026-02-24 10:05 - Dokumentation: SECURITY.md & CVE_HISTORY.md erstellt
```

---

## Werkzeuge für Security-Monitoring

### Manuelle Scans
```bash
# Python Dependencies
pip-audit

# Nach neuester Version checken
pip list --outdated

# Sicherheits-Check
safety check
```

### Automatisierte Scans
- **Snyk:** Täglich 06:00 UTC
- **CodeQL:** Bei jedem Push
- **Dependabot:** Bei neuen Releases

---

**Letzte Aktualisierung:** 2026-02-24
**Nächste Review:** 2026-03-24
**Verantwortlich:** Security Team / Maintainers
