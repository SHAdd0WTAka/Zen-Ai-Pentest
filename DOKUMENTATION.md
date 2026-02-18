# Zen AI Pentest - Setup Dokumentation

> **Datum:** 2026-02-18  
> **Autor:** Kimi AI (im Devcontainer)  
> **Status:** ✅ Alle Services laufen

---

## Übersicht

Diese Dokumentation beschreibt alle Schritte, die zur Wiederherstellung der Zen AI Pentest Umgebung durchgeführt wurden.

---

## Durchgeführte Schritte

### 1. Devcontainer Einrichtung

**Problem:** Devcontainer konnte nicht gestartet werden  
**Ursachen:**
- Debian 'trixie' wird nicht von Docker-in-Docker unterstützt
- `.env` Datei enthält `export` Syntax (nicht Docker-kompatibel)
- `.devcontainer/bash_history` fehlte

**Lösungen:**

```json
// .devcontainer/devcontainer.json - ÄNDERUNGEN:

// Vorher:
"image": "mcr.microsoft.com/devcontainers/python:3.11"

// Nachher:
"image": "mcr.microsoft.com/devcontainers/python:3.11-bookworm"
```

```json
// Vorher:
"runArgs": [
  "--env-file",
  "${localWorkspaceFolder}/.env"
]

// Nachher:
"runArgs": []
```

```bash
# Erstellt:
touch .devcontainer/bash_history
```

**Befehle:**
```bash
devcontainer up --workspace-folder .
```

---

### 2. API Reparatur (PostgreSQL)

**Problem:** API zeigte "unhealthy"  
**Ursache:** PostgreSQL-Container war gestoppt  
**Fehler:** `could not translate host name "postgres" to address`

**Lösung:**
```bash
# PostgreSQL Container starten
docker start zen-postgres

# API neu starten
docker restart zen-api
```

**Ergebnis:**
- ✅ zen-api: healthy
- ✅ zen-postgres: healthy
- ✅ API erreichbar unter: http://localhost:8000/health

---

### 3. Frontend Reparatur

**Problem:** Port 3000 war nicht erreichbar  
**Ursache:** Frontend-Container hatte keine Port-Mappings und beendete sich sofort

**Lösung - Einfaches HTML-Frontend:**

Da das originale Frontend-Image nur Source-Code enthielt (keinen Build) und Node.js Versionskonflikte hatte, wurde ein alternatives Frontend erstellt:

```bash
# Verzeichnis erstellt
mkdir -p ./frontend-simple

# Einfaches HTML-Frontend mit Python HTTP-Server
# (siehe frontend-simple/index.html)
```

**Container-Start:**
```bash
docker run -d \
  --name zen-frontend \
  --network host \
  -v /mnt/c/Users/Ataka/zen-ai-pentest/frontend-simple:/app \
  -w /app \
  python:3.11-slim \
  python -m http.server 3000 --bind 0.0.0.0
```

**Wichtig:** `--network host` ist erforderlich, damit das Frontend im Browser auf `localhost:8000` zugreifen kann.

---

### 4. Windows Firewall (PowerShell)

**Problem:** Windows blockierte Port 3000  
**Lösung:**

```powershell
# Als Administrator in PowerShell:
netsh advfirewall firewall add rule name="WSL2 Port 3000" dir=in action=allow protocol=tcp localport=3000
```

---

### 5. Chromium Installation

**Installation im Devcontainer:**
```bash
devcontainer exec --workspace-folder . sudo apt-get update
devcontainer exec --workspace-folder . sudo apt-get install -y chromium
```

**Version:** Chromium 145.0.7632.75

---

## Aktueller Systemstatus

### Laufende Container

| Container | Status | Ports | Beschreibung |
|-----------|--------|-------|--------------|
| zen-api | ✅ healthy | 8000:8000 | FastAPI Backend |
| zen-frontend | ✅ running | 3000:3000 | Web UI |
| zen-postgres | ✅ healthy | 5432:5432 | PostgreSQL DB |
| zen-celery | ✅ running | - | Background Worker |
| competent_curie | ✅ running | - | Devcontainer |

### Verfügbare URLs

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | http://localhost:3000 | ✅ Online |
| **API Docs** | http://localhost:8000/docs | ✅ Online |
| **Health Check** | http://localhost:8000/health | ✅ Online |

---

## Bekannte Einschränkungen

### API-Status im Frontend zeigt "Offline"

**Ursache:** Browser CORS-Policy blockiert Anfragen von localhost:3000 an localhost:8000

**Workaround:** 
- API direkt im Browser testen: http://localhost:8000/health
- Oder Terminal: `curl http://localhost:8000/health`

**Technische Details:**
- Das Frontend läuft mit `--network host`
- JavaScript im Browser unterliegt Same-Origin-Policy
- Die API liefert keine CORS-Headers

---

## Nützliche Befehle

### Container verwalten
```bash
# Alle Container anzeigen
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs anzeigen
docker logs zen-api
docker logs zen-frontend
docker logs zen-postgres

# Container neu starten
docker restart zen-api
docker restart zen-frontend
```

### Devcontainer
```bash
# Devcontainer starten
devcontainer up --workspace-folder .

# In Devcontainer einloggen
devcontainer exec --workspace-folder . /bin/bash
```

### Tests
```bash
# API Health Check
curl http://localhost:8000/health

# Frontend Test
curl http://localhost:3000 | head
```

---

## Dateien und Verzeichnisse

```
/mnt/c/Users/Ataka/zen-ai-pentest/
├── .devcontainer/
│   ├── devcontainer.json      # Konfiguriert (bookworm, runArgs)
│   ├── bash_history           # Erstellt
│   └── post-create.sh
├── frontend-simple/           # NEU ERSTELLT
│   └── index.html            # Einfaches Dashboard
├── DOKUMENTATION.md          # Diese Datei
└── docker-compose.yml        # Original (enthält keinen Frontend-Service)
```

---

## Zusammenfassung

✅ **Devcontainer:** Läuft mit Debian Bookworm  
✅ **API:** Healthy, PostgreSQL verbunden  
✅ **Frontend:** Ersatz-HTML läuft auf Port 3000  
✅ **Firewall:** Port 3000 freigegeben  
✅ **Chromium:** Im Devcontainer installiert  

---

## Nächste Schritte (optional)

1. **CORS aktivieren** in der API für vollständige Frontend-Funktionalität
2. **Original-Frontend bauen** mit `npm run build` statt Ersatz-HTML
3. **HTTPS** für produktiven Einsatz einrichten
4. **Authentifizierung** im Frontend implementieren

---

*Dokumentation erstellt am: 2026-02-18*  
*Letzte Aktualisierung: 2026-02-18 23:25 Uhr*

---

## Update 2026-02-18 23:35 - CORS Fix

### Problem
API-Status im Frontend zeigte "NetworkError" / "Offline" trotz laufender API.

### Ursache
Doppelte CORS-Konfiguration:
- `api/main.py` erwartet komma-getrennte Liste
- `api/core/config.py` (pydantic-settings) erwartet JSON-Array
- Konflikt beim Parsen der `CORS_ORIGINS` Environment Variable

### Lösung
API **ohne** `CORS_ORIGINS` Environment Variable starten:
```bash
docker run -d \
  --name zen-api \
  --network zen-ai-pentest_zen-network \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@zen-postgres:5432/zen_pentest" \
  -e JWT_SECRET_KEY="dev-secret-key" \
  -e ADMIN_PASSWORD="admin" \
  zen-ai-pentest-api
```

Die API verwendet dann die Default-Werte aus `main.py`:
```python
CORS_ORIGINS="http://localhost:3000,http://localhost:8000"
```

### Ergebnis
CORS Headers jetzt korrekt:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-credentials: true
access-control-expose-headers: X-Request-ID
```

Frontend kann jetzt API-Status abrufen! ✅
