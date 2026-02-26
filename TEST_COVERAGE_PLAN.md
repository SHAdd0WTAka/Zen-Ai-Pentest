# 🎯 80% Coverage Plan für Zen-AI-Pentest

## Ziel
- **Zeitraum:** 3-5 Tage
- **Ziel-Coverage:** 40-50% (gesamt)
- **Strategie:** Focus auf 20 High-Impact Module

---

## 📊 Ausgangslage

| Metrik | Wert |
|--------|------|
| Gesamt-Coverage | 0.4% |
| Getestete Lines | 273 / 51,044 |
| api/schemas.py | ✅ 99.6% (fertig) |

## 🎯 Ziel-Module (Top 20)

| Tag | Module | Lines | Schwierigkeit | Tools |
|-----|--------|-------|---------------|-------|
| **Tag 1** | api/main.py, api/auth.py, core/config.py | ~1,000 | Einfach | Pynguin + Manuell |
| **Tag 2** | core/cache.py, core/health_check.py, core/plugin_system.py | ~1,500 | Mittel | Hypothesis |
| **Tag 3** | database/models.py, database/crud.py, database/cve_database.py | ~1,000 | Mittel | Factory Boy |
| **Tag 4** | tools/nmap_integration.py, autonomous/agent_loop.py, risk_engine/* | ~1,500 | Schwer | Mocks |
| **Tag 5** | api/routes/*, Remaining tests, Integration | ~3,000 | Mittel | API-Tests |

**Gesamt:** ~7,939 Lines → 6,351 neue getestete Lines bei 80%
**Coverage-Zuwachs:** +12.4%

---

## 🚀 Tagespläne

### Tag 1: API Foundation
**Ziel:** 3 Module, ~300 Tests, Coverage +5%

```bash
# Module
- api/main.py (720 lines)
- api/auth.py (66 lines)
- api/core/config.py (12 lines)

# Tools
pynguin --module-name api.main --output-path tests/generated/
pynguin --module-name api.auth --output-path tests/generated/

# Manuell für Config
# Teste alle Config-Variablen und Defaults
```

**Erfolgskriterien:**
- [ ] api/main.py: 80% Coverage
- [ ] api/auth.py: 80% Coverage
- [ ] api/core/config.py: 100% Coverage

---

### Tag 2: Core Infrastructure
**Ziel:** 3 Core-Module, ~400 Tests, Coverage +3%

```bash
# Module
- core/cache.py (550 lines)
- core/health_check.py (499 lines)
- core/plugin_system.py (428 lines)

# Tools
# Hypothesis für Cache-Validierung
# Manuell für Health Checks
# Pynguin für Plugin System
```

**Erfolgskriterien:**
- [ ] core/cache.py: 80% Coverage
- [ ] core/health_check.py: 80% Coverage
- [ ] core/plugin_system.py: 80% Coverage

---

### Tag 3: Database Layer
**Ziel:** 3 DB-Module, ~300 Tests, Coverage +2%

```bash
# Module
- database/models.py (241 lines)
- database/crud.py (59 lines)
- database/cve_database.py (292 lines)

# Tools
# Factory Boy für Model-Generation
# SQLite in-memory für Tests
```

**Erfolgskriterien:**
- [ ] database/models.py: 80% Coverage
- [ ] database/crud.py: 100% Coverage
- [ ] database/cve_database.py: 80% Coverage

---

### Tag 4: Autonomous Agents & Tools
**Ziel:** 4 komplexe Module, ~400 Tests, Coverage +3%

```bash
# Module
- autonomous/agent_loop.py (546 lines)
- autonomous/exploit_validator.py (469 lines)
- tools/nmap_integration.py (409 lines)
- risk_engine/false_positive_engine.py (547 lines)

# Tools
# Extensive Mocking für externe Tools
# Hypothesis für Risk Calculations
```

**Erfolgskriterien:**
- [ ] autonomous/agent_loop.py: 60% Coverage (komplex)
- [ ] autonomous/exploit_validator.py: 70% Coverage
- [ ] tools/nmap_integration.py: 70% Coverage
- [ ] risk_engine/false_positive_engine.py: 70% Coverage

---

### Tag 5: API Routes & Integration
**Ziel:** API-Integration Tests, ~500 Tests, Coverage +2%

```bash
# Module
- api/routes/auth.py
- api/routes/scans.py
- api/routes/agents.py
- api/rate_limiter_v2.py (257 lines)

# Tools
# FastAPI TestClient
# End-to-End Tests
```

**Erfolgskriterien:**
- [ ] Alle API-Routes mit 60%+ Coverage
- [ ] Integration Tests laufen durch
- [ ] Gesamt-Coverage ≥ 40%

---

## 🛠️ Automatisierung

### Script: Automatische Test-Generierung
```bash
# Starte automatische Generation
python scripts/generate_tests.py

# Track Progress
python scripts/coverage_tracker.py --analyze
```

### CI Integration
```yaml
# .github/workflows/coverage.yml
- name: Run Coverage
  run: |
    pytest tests/ --cov=. --cov-fail-under=40

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

---

## 📈 Tracking

### Tägliche Messung
```bash
# Am Ende jedes Tages
coverage run -m pytest tests/
coverage report --show-missing
coverage html
```

### Wichtige Metriken
- **Lines Covered:** Ziel +6,351 neue Lines
- **Files ≥80%:** Ziel 20 Dateien
- **Total Coverage:** Ziel 40-50%

---

## 🎁 Bonus: Crawl4AI Integration (parallel)

Während der Tests auch das neue Tool integrieren:
- `tools/crawl4ai_integration.py` (bereits erstellt)
- Tests für Crawl4AI: ~50 Tests
- Fügt weitere +0.5% Coverage hinzu

---

## ✅ Erfolgs-Definition

**Tag 5 Ende:**
- [ ] Mindestens 40% Gesamt-Coverage
- [ ] 20 Module mit je ≥60% Coverage
- [ ] Alle Tests laufen in CI durch
- [ ] OpenSSF Badge auf "in progress" mit Roadmap

**Stretch Goal:**
- [ ] 50% Gesamt-Coverage
- [ ] 15 Module mit ≥80% Coverage

---

## 🆘 Troubleshooting

### Wenn Pynguin nicht funktioniert:
```bash
# Fallback: Hypothesis Ghostwriter
python -m hypothesis write module.name
```

### Wenn Tests zu langsam:
```bash
# Parallel ausführen
pytest -n auto tests/
```

### Wenn Coverage nicht steigt:
```bash
# Schau welche Lines fehlen
coverage report --show-missing | head -50
```

---

## 📝 Daily Standup Fragen

1. **Was hast du gestern geschafft?**
   - Module X: Y% Coverage erreicht

2. **Was machst du heute?**
   - Module Z testen

3. **Gibt es Blocker?**
   - Import-Probleme / Mocking-Probleme

---

**Start:** Tag 1 - API Foundation
**Soll ich mit dem ersten Modul (api/main.py) beginnen?** 🚀
