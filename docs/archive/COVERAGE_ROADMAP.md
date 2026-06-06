# Coverage Roadmap: 6.57% → 80%

## Priorisierung nach Modul-Größe und Wichtigkeit

### Phase 1: Core Module (Ziel: +20% Coverage)
- [ ] `core/cache.py` - Wichtig für Performance
- [ ] `core/state_machine.py` - Zustandsverwaltung
- [ ] `core/workflow_engine.py` - Workflow-Logik
- [ ] `core/orchestrator.py` - Hauptorchestrierung
- [ ] `core/tool_manager.py` - Tool-Verwaltung

**Aufwand:** ~50 neue Tests
**Erwarteter Impact:** +15-20% Coverage

### Phase 2: API Layer (Ziel: +15% Coverage)
- [ ] `api/main.py` - FastAPI Endpunkte
- [ ] `api/auth.py` - Authentifizierung
- [ ] `api/routes/*.py` - Alle Route-Module
- [ ] `api/schemas.py` - Pydantic Models

**Aufwand:** ~40 neue Tests
**Erwarteter Impact:** +10-15% Coverage

### Phase 3: Database Models (Ziel: +10% Coverage)
- [ ] `database/models.py` - CRUD Operations
- [ ] `database/auth_models.py` - Auth Models
- [ ] `database/crud.py` - Datenbank-Logik

**Aufwand:** ~30 neue Tests
**Erwarteter Impact:** +8-10% Coverage

### Phase 4: Tools Integration (Ziel: +15% Coverage)
- [ ] `tools/nmap_integration.py`
- [ ] `tools/sqlmap_integration.py`
- [ ] `tools/nuclei_integration.py`
- [ ] `tools/ffuf_integration.py`
- [ ] `tools/gobuster_integration.py`
- [ ] Und 20+ weitere Tools...

**Aufwand:** ~100 neue Tests
**Erwarteter Impact:** +15-20% Coverage

### Phase 5: Agents (Ziel: +10% Coverage)
- [ ] `agents/agent_base.py`
- [ ] `agents/agent_orchestrator.py`
- [ ] `agents/research_agent.py`
- [ ] `agents/analysis_agent.py`
- [ ] `agents/exploit_agent.py`

**Aufwand:** ~40 neue Tests
**Erwarteter Impact:** +8-10% Coverage

### Phase 6: Utils & Helpers (Ziel: +5% Coverage)
- [ ] `utils/helpers.py`
- [ ] `utils/security.py`
- [ ] `utils/async_fixes.py`

**Aufwand:** ~20 neue Tests
**Erwarteter Impact:** +3-5% Coverage

---

## Gesamtschätzung

| Phase | Tests | Zeitaufwand | Coverage-Impact |
|-------|-------|-------------|-----------------|
| 1 | 50 | 4h | +20% |
| 2 | 40 | 3h | +15% |
| 3 | 30 | 2h | +10% |
| 4 | 100 | 8h | +15% |
| 5 | 40 | 3h | +10% |
| 6 | 20 | 1h | +5% |
| **Total** | **~280** | **~21h** | **+75%** |

**Aktuell:** 6.57%
**Ziel:** 80%+
**Gap:** ~73%

---

## Quick-Win: Automatische Test-Generierung

Für einfache Dataclasses und Models können wir Templates verwenden:

```bash
# Alle Models finden, die 0% Coverage haben
grep -r "^class.*:" database/ api/ core/ | grep -v test | head -30

# Schnelle Tests für __init__ Methoden generieren
python scripts/generate_init_tests.py
```

---

## Empfohlene nächste Schritte

1. **Fix verbleibende Import-Fehler** (~30 Min)
2. **Core Module Tests schreiben** (~4 Stunden)
3. **API Routes mit TestClient testen** (~3 Stunden)
4. **Integration Tests für Tool-Workflows** (~4 Stunden)
