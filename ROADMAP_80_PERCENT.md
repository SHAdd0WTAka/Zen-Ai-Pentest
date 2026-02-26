# Roadmap: 8.65% → 80% Coverage

## Realistische Schätzung

| Phase | Tests nötig | Zeit | Coverage | Kumulative |
|-------|-------------|------|----------|------------|
| Aktuell | 279 | 5h | 8.65% | 8.65% |
| **Phase 1** | +300 | 4h | +10% | **18%** |
| **Phase 2** | +500 | 5h | +12% | **30%** |
| **Phase 3** | +800 | 6h | +15% | **45%** |
| **Phase 4** | +1000 | 8h | +17% | **62%** |
| **Phase 5** | +1200 | 8h | +12% | **74%** |
| **Phase 6** | +800 | 5h | +6% | **80%** |
| **Total** | **~4700** | **~35h** | **+71%** | **80%** |

## Phase 1: Core Module Deep Tests (+10%)

### Ziel: 18% Coverage
- [ ] `core/orchestrator.py` - Full workflow tests
- [ ] `core/state_machine.py` - All state transitions
- [ ] `core/workflow_engine.py` - Task execution tests
- [ ] `core/tool_manager.py` - Tool registration & execution
- [ ] `core/cache.py` - Already good (~85%)

**Tests nötig:** ~300  
**Zeit:** 4 Stunden

## Phase 2: API Deep Tests (+12%)

### Ziel: 30% Coverage
- [ ] All API routes with auth
- [ ] Request/response validation
- [ ] Error handling (400, 401, 403, 404, 422)
- [ ] Edge cases (empty body, large payloads)
- [ ] All Pydantic schemas

**Tests nötig:** ~500  
**Zeit:** 5 Stunden

## Phase 3: Database Deep Tests (+15%)

### Ziel: 45% Coverage
- [ ] All CRUD operations
- [ ] Relationships (User-Scan-Finding)
- [ ] Transactions & rollbacks
- [ ] Query optimization tests
- [ ] All model methods

**Tests nötig:** ~800  
**Zeit:** 6 Stunden

## Phase 4: Tools Deep Tests (+17%)

### Ziel: 62% Coverage
- [ ] All 25+ tools with mocked subprocess
- [ ] Output parsing for each tool
- [ ] Error handling for each tool
- [ ] Result validation
- [ ] Integration tests

**Tests nötig:** ~1000  
**Zeit:** 8 Stunden

## Phase 5: Agents Deep Tests (+12%)

### Ziel: 74% Coverage
- [ ] Agent orchestration
- [ ] Message passing
- [ ] Multi-agent workflows
- [ ] Error recovery
- [ ] State management

**Tests nötig:** ~1200  
**Zeit:** 8 Stunden

## Phase 6: Utils & Edge Cases (+6%)

### Ziel: 80% Coverage
- [ ] All utility functions
- [ ] Error handlers
- [ ] Edge cases
- [ ] Integration tests
- [ ] End-to-end tests

**Tests nötig:** ~800  
**Zeit:** 5 Stunden

---

## Schnell-Start: Phase 1

```bash
# Run current tests
pytest tests/ -v --tb=no

# Check coverage
pytest tests/ --cov=. --cov-report=term

# Generate more tests
python scripts/generate_mass_tests.py
```

## Empfohlene Reihenfolge

1. **Heute (4h):** Phase 1 - Core Module
2. **Morgen (5h):** Phase 2 - API Deep
3. **Tag 3 (6h):** Phase 3 - Database
4. **Tag 4-5 (8h):** Phase 4 - Tools
5. **Tag 6-7 (8h):** Phase 5 - Agents
6. **Tag 8 (5h):** Phase 6 - Utils & Polish

**Gesamt: 8 Tage, ~35 Stunden**

---

## Alternative: Smart 80%

Nur wichtige Module auf 80%, Rest auf 50%:

| Modul | Ziel-Coverage | Tests |
|-------|---------------|-------|
| core/* | 80% | 500 |
| api/* | 80% | 600 |
| database/* | 80% | 400 |
| tools/* | 60% | 800 |
| agents/* | 60% | 400 |
| utils/* | 50% | 200 |
| **Total** | **~70%** | **~2900** |

**Zeit: ~20 Stunden (4-5 Tage)**

---

**Entscheidung:**
- **A:** Vollständiger 80% Plan (35h, 8 Tage)
- **B:** Smart 80% Plan (20h, 4-5 Tage)
- **C:** Aktueller Stand ist OK, andere Features priorisieren
