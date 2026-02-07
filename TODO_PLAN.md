# 🗺️ Zen-AI Pentest - Master Plan

**Stand:** 2026-02-07  
**Ziel:** Produktionsreifes AI-Powered Pentesting Framework

---

## 🔴 KRITISCH (Sofort erledigen)

### 1. Security & Keys
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 1.1 | ~~API Key aus History entfernen~~ | ⚠️ Blockiert (Branch Protection) | 🔴 |
| 1.2 | Pre-commit Hook für Keys erstellen | ⏳ Offen | 🔴 |
| 1.3 | SECURITY.md aktualisieren | ⏳ Offen | 🟡 |

**Empfehlung:** Key ist revoked → Risiko minimiert

### 2. Docker Stabilität
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 2.1 | ~~Celery Fix~~ | ✅ Erledigt | ✅ |
| 2.2 | Docker Compose vollständig testen | ⏳ Offen | 🔴 |
| 2.3 | Health Checks für alle Services | ⏳ Offen | 🟡 |
| 2.4 | Docker Volume Persistenz prüfen | ⏳ Offen | 🟡 |

---

## 🟡 HOCH (Diese Woche)

### 3. Tests & Qualität
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 3.1 | ~~Basis Tests erstellt~~ | ✅ Erledigt | ✅ |
| 3.2 | Test Coverage auf 80% erhöhen | ⏳ 45% aktuell | 🟡 |
| 3.3 | Integration Tests für Docker | ⏳ Offen | 🟡 |
| 3.4 | Mock für externe APIs | ⏳ Teilweise | 🟡 |
| 3.5 | CI/CD Pipeline stabilisieren | ⏳ 9/10 OK | 🟡 |

### 4. API & Backend
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 4.1 | API Authentication implementieren | ⏳ Offen | 🔴 |
| 4.2 | Rate Limiting | ⏳ Offen | 🟡 |
| 4.3 | API Dokumentation (OpenAPI/Swagger) | ⏳ Teilweise | 🟡 |
| 4.4 | Error Handling verbessern | ⏳ Offen | 🟡 |
| 4.5 | Logging & Monitoring | ⏳ Basis | 🟡 |

### 5. Frontend
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 5.1 | React App stabilisieren | ⏳ Unbekannt | 🟡 |
| 5.2 | Login/Auth UI | ⏳ Offen | 🔴 |
| 5.3 | Dashboard für Scan-Ergebnisse | ⏳ Offen | 🟡 |
| 5.4 | Persona Selector UI | ⏳ Offen | 🟡 |

---

## 🟢 MITTEL (Diesen Monat)

### 6. Features
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 6.1 | Weitere Personas (webapp, api, crypto) | ⏳ Offen | 🟢 |
| 6.2 | Export Formate (PDF, JSON, XML) | ⏳ Offen | 🟢 |
| 6.3 | Report Templates | ⏳ Offen | 🟢 |
| 6.4 | Scan Scheduler | ⏳ Offen | 🟢 |
| 6.5 | Notification System (Slack, Email) | ⏳ Teilweise | 🟢 |

### 7. Dokumentation
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 7.1 | ~~GitHub Pages~~ | ✅ Erledigt | ✅ |
| 7.2 | ~~Installation Guide~~ | ✅ Erledigt | ✅ |
| 7.3 | API Tutorial | ⏳ Offen | 🟢 |
| 7.4 | Video Tutorials | ⏳ Offen | 🔵 |
| 7.5 | Beispiel-Workflows | ⏳ Offen | 🟢 |

---

## 🔵 NIEDRIG (Backlog)

### 8. Optimierungen
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 8.1 | Performance Tuning | ⏳ Offen | 🔵 |
| 8.2 | Caching Layer | ⏳ Redis vorhanden | 🔵 |
| 8.3 | Multi-Threading für Scans | ⏳ Offen | 🔵 |
| 8.4 | Plugin System | ⏳ Offen | 🔵 |
| 8.5 | Helm Chart für Kubernetes | ⏳ Offen | 🔵 |

### 9. Community
| # | Task | Status | Priorität |
|---|------|--------|-----------|
| 9.1 | Contributing Guidelines | ⏳ Vorhanden | ✅ |
| 9.2 | Issue Templates | ⏳ Offen | 🔵 |
| 9.3 | Discord/Forum | ⏳ Offen | 🔵 |
| 9.4 | Showcase/Beispiele | ⏳ Offen | 🔵 |

---

## 📊 Zusammenfassung

| Kategorie | Anzahl | Erledigt | Offen |
|-----------|--------|----------|-------|
| 🔴 Kritisch | 5 | 2 | 3 |
| 🟡 Hoch | 15 | 2 | 13 |
| 🟢 Mittel | 10 | 2 | 8 |
| 🔵 Niedrig | 9 | 0 | 9 |
| **Gesamt** | **39** | **6** | **33** |

---

## 🎯 Empfohlene Roadmap

### Woche 1 (Diese Woche)
1. ✅ Docker stabilisieren (Celery ✅)
2. Pre-commit Hook für Keys
3. API Auth implementieren
4. Test Coverage erhöhen

### Woche 2
1. Frontend Login/Auth
2. API Rate Limiting
3. Health Checks
4. Export Formate

### Woche 3
1. Dashboard UI
2. Report Templates
3. Weitere Personas
4. Notification System

### Woche 4
1. Performance Tuning
2. Video Tutorials
3. Kubernetes Support
4. Community Aufbau

---

## 🚀 Schnelle Wins (Heute machbar)

```bash
# 1. Pre-commit Hook erstellen
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
if git diff --cached | grep -E "(sk-or-|sk-)[a-zA-Z0-9]{20,}"; then
    echo "ERROR: API Key gefunden!"
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit

# 2. Health Check Endpunkt testen
curl http://localhost:8000/health

# 3. Test Coverage checken
pytest --cov=tools tests/

# 4. Docker komplett testen
docker-compose -f docker-compose.test.yml up
```

---

Letzte Aktualisierung: $(Get-Date -Format "yyyy-MM-dd HH:mm")
