# SIEM Integration - 3 Betriebsmodi

Dieses Dokument beschreibt die 3 verfügbaren SIEM-Integrationsmodi.

---

## Modus 1: Mock-SIEM (Demo/Testing)

**Für:** Entwicklung, Demos, Tests ohne echte Daten

```bash
# 1. API starten
python -m api.main

# 2. Mock-SIEM verbinden
curl -X POST http://localhost:8000/api/v1/siem/connect \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Mock SIEM",
    "type": "mock",
    "url": "mock://demo",
    "api_key": "demo",
    "is_mock": true
  }'

# 3. Events senden
curl -X POST http://localhost:8000/api/v1/siem/events \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "high",
    "event_type": "xss",
    "source": "192.168.1.1",
    "target": "webapp.com",
    "description": "XSS detected"
  }'

# 4. Events abrufen
curl http://localhost:8000/api/v1/siem/events
```

**Features:**
- Lokale Event-Speicherung (im Speicher)
- Keine externen Abhängigkeiten
- Auto-Mock Mode (funktioniert auch ohne Verbindung)
- Events werden lokal gespeichert und können abgerufen werden

---

## Modus 2: Standalone (Ohne SIEM, Ohne API)

**Für:** Jeder kann es sofort nutzen, keine Infrastruktur nötig

```bash
# Schneller Scan - sofort startklar
python standalone_scan.py --target example.com

# Mit Optionen
python standalone_scan.py \
  --target 192.168.1.1 \
  --scan-type full \
  --output-dir ./reports
```

**Scan-Typen:**
- `quick` - Schnelle Analyse (~1s)
- `full` - Vollständige Analyse (~30s)
- `deep` - Tiefe Analyse mit allen Modulen (~2min)

**Output-Formate:**
- `JSON` - Maschinenlesbar für Automation
- `Markdown` - Menschenlesbarer Report
- `CSV` - Für Excel/Tabellenkalkulation

**Beispiel-Output:**
```
reports/
├── scan_example.com_20260204_153722.json
├── scan_example.com_20260204_153722.md
└── scan_example.com_20260204_153722.csv
```

---

## Modus 3: Echt-SIEM (Produktion)

**Für:** Enterprise-Umgebungen mit existierendem SIEM

### Unterstützte Systeme:

| SIEM | Formate | Auth |
|------|---------|------|
| Splunk | json, cef | HEC Token |
| Elastic | json | API Key |
| Azure Sentinel | json | Workspace ID |
| IBM QRadar | leef, json | API Token |
| Rapid7 | json | API Key |
| Custom | Alle | Headers |

### Verbindung herstellen:

```bash
# Splunk Beispiel
curl -X POST http://localhost:8000/api/v1/siem/connect \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Splunk",
    "type": "splunk",
    "url": "https://splunk.company.com:8088",
    "api_key": "your-hec-token",
    "index": "security"
  }'
```

---

## Schnellvergleich

| Feature | Mock-SIEM | Standalone | Echt-SIEM |
|---------|-----------|------------|-----------|
| **API nötig** | Ja | Nein | Ja |
| **SIEM nötig** | Nein (Mock) | Nein | Ja |
| **Setup** | API starten | Sofort | SIEM config |
| **Events** | Lokal | Lokale Reports | Externes SIEM |
| **Nutzer** | Entwickler | Jeder | Security-Teams |
| **Use Case** | Demo/Test | Quick-Scan | Produktion |

---

## Empfohlener Workflow

```
┌─────────────────┐
│  Entwicklung    │───► Mock-SIEM (Tests/Demos)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Jeder User    │───► Standalone (Sofort nutzbar)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Enterprise     │───► Echt-SIEM (Produktion)
└─────────────────┘
```

---

## Test-Kommandos

```bash
# Alle Modi testen

# 1. Mock-SIEM Test
python test_mock_siem.py

# 2. Standalone Test
python standalone_scan.py --target example.com

# 3. API Health Check
curl http://localhost:8000/health
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| API nicht erreichbar | `python -m api.main` starten |
| Port 8000 belegt | `lsof -ti:8000 \| xargs kill -9` |
| DuckDuckGo failed | Normal, funktioniert trotzdem lokal |
| Keine Reports | `--output-dir` prüfen |

---

**Alle 3 Modi sind vollständig integriert und einsatzbereit!** 🎯
