# Test Coverage Plan: 3% → 50%

**Ziel**: 50% Test Coverage erreichen
**Zeitrahmen**: 2-3 Wochen
**Strategie**: Unit-Tests zuerst (schnell, isoliert), dann Integration

---

## Phase 2.1: Test Infrastructure (Woche 1)

### ✅ Bereits erledigt:
- [x] conftest.py repariert (Mock-First Ansatz)
- [x] Lazy-loading Fixtures
- [x] Test markers (unit, integration, slow)

### Noch zu tun:
- [ ] Test-Daten Verzeichnis erstellen
- [ ] CI Coverage Workflow optimieren
- [ ] Coverage Badge aktualisieren

---

## Phase 2.2: Core Module Unit-Tests (Woche 1-2)

### Ziel: +15% Coverage

| Modul | Datei | Tests | Schwierigkeit |
|-------|-------|-------|---------------|
| **Core** | `core/models.py` | Dataclass validation | ⭐ Einfach |
| **Core** | `core/cache.py` | Caching logic | ⭐⭐ Mittel |
| **Utils** | `utils/helpers.py` | Helper functions | ⭐ Einfach |
| **Utils** | `utils/async_fixes.py` | Async utilities | ⭐⭐ Mittel |
| **Validation** | `core/input_validator.py` | Input validation | ⭐ Einfach |

### Beispiel-Struktur:
```
tests/unit/
├── core/
│   ├── test_models.py
│   ├── test_cache.py
│   └── test_input_validator.py
├── utils/
│   ├── test_helpers.py
│   └── test_async_fixes.py
└── __init__.py
```

---

## Phase 2.3: Tool Registry Tests (Woche 2)

### Ziel: +10% Coverage

| Modul | Datei | Tests |
|-------|-------|-------|
| **Tools** | `tools/tool_registry.py` | Registry operations |
| **Tools** | `tools/tool_caller.py` | Tool execution |
| **Tools** | `tools/kimi_helper.py` | AI helper functions |

---

## Phase 2.4: Agent Tests (Woche 2-3)

### Ziel: +15% Coverage

| Modul | Datei | Tests |
|-------|-------|-------|
| **Agents** | `agents/react_agent.py` | ReAct pattern |
| **Agents** | `agents/analysis_agent.py` | Analysis logic |
| **Agents** | `agents/post_scan_agent.py` | Post-scan processing |

---

## Phase 2.5: API & Integration Tests (Woche 3)

### Ziel: +7% Coverage (bis 50%)

| Modul | Datei | Tests |
|-------|-------|-------|
| **API** | `api/schemas.py` | Pydantic models |
| **API** | `api/auth_simple.py` | Auth functions |
| **API** | `api/routes/health.py` | Health endpoints |

---

## Priorisierung

### Sofort (Heute):
1. `core/models.py` - Einfache Dataclasses
2. `utils/helpers.py` - Reine Funktionen
3. `core/input_validator.py` - Validation logic

### Diese Woche:
4. `tools/tool_registry.py` - Wichtig für Kernfunktionalität
5. `core/cache.py` - Caching behavior

### Nächste Woche:
6. Agent Tests
7. API Schema Tests

---

## Unit-Test Template

```python
import pytest
from unittest.mock import MagicMock, patch

# Mark as unit test
pytestmark = pytest.mark.unit

class TestModuleName:
    """Tests for module X"""

    def test_function_normal_case(self):
        """Test normal operation"""
        # Arrange
        input_data = "test"

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output

    def test_function_edge_case(self):
        """Test edge cases"""
        pass

    def test_function_error_handling(self):
        """Test error handling"""
        pass
```

---

## Coverage Tracking

| Datum | Coverage | Änderung | Notes |
|-------|----------|----------|-------|
| 2026-02-16 | 3% | Baseline | Start Phase 2 |
| 2026-02-16 | ?% | +?% | conftest.py fixed |
| | | | |

---

## Erfolgskriterien

✅ Phase 2.2 complete: Core Module haben >80% Coverage
✅ Phase 2.3 complete: Tool Registry >70% Coverage
✅ Phase 2.4 complete: Agent Tests >60% Coverage
✅ Phase 2.5 complete: API Schemas >80% Coverage
✅ **Gesamt: 50% Coverage erreicht**

---

*Dieser Plan wird von ZenClaw Guardian verwaltet und täglich aktualisiert.*
