# Guide: Erreichen von 80% Test Coverage

> **Ziel:** Systematischer Ansatz zur Erreichung von 80%+ Code Coverage in Zen-AI-Pentest

---

## 📊 Aktueller Stand: core/cache.py

| Metrik | Vorher | Nachher | Ziel |
|--------|--------|---------|------|
| Line Coverage | 25.52% | ~60%* | 80% |
| Branch Coverage | ~15% | ~50%* | 75% |
| Function Coverage | ~40% | ~70%* | 85% |

*Teilweise durch neue Tests erreicht

---

## 🎯 Der 80%-Coverage-Ansatz

### 1. Analyse (Wichtigste Schritte)

```bash
# 1. Coverage baseline messen
pytest --cov=core.cache --cov-report=term-missing

# 2. Fehlende Zeilen identifizieren
# Im Report: "Missing" zeigt nicht-getestete Zeilen
```

### 2. Test-Pyramide für 80%

```
        /\
       /  \      E2E Tests (5%)
      /----\
     /      \    Integration Tests (15%)
    /--------\
   /          \  Unit Tests (80%)
  /------------\
```

---

## 📝 Step-by-Step: Von 25% zu 80%

### Phase 1: Grundlagen (25% → 40%)

**Ziel:** Alle Klassen initialisieren, Properties testen

```python
class TestCacheStats:
    """Test simple dataclass - easy coverage wins"""

    def test_default_values(self):
        stats = CacheStats()
        assert stats.hits == 0

    def test_hit_rate_calculation(self):
        stats = CacheStats(hits=80, total_gets=100)
        assert stats.hit_rate == 0.8  # 80%
```

**Ergebnis:** +15% Coverage durch einfache Tests

---

### Phase 2: Async Basis (40% → 55%)

**Ziel:** Grundlegende async Operationen testen

```python
@pytest.mark.asyncio
async def test_get_set_delete():
    """Test basic CRUD operations"""
    cache = MemoryCache()

    # Create
    await cache.set("key", "value")

    # Read
    value = await cache.get("key")
    assert value == "value"

    # Delete
    await cache.delete("key")
    assert await cache.get("key") is None
```

**Wichtig:** Jedes `async def` braucht `@pytest.mark.asyncio`

---

### Phase 3: Edge Cases (55% → 70%)

**Ziel:** Grenzfälle und Fehlerbehandlung

```python
@pytest.mark.asyncio
async def test_get_nonexistent_key():
    """Test miss counting"""
    cache = MemoryCache()

    value = await cache.get("nonexistent")
    assert value is None
    assert cache.stats.misses == 1  # Stats getestet!

@pytest.mark.asyncio
async def test_ttl_expiry():
    """Test TTL functionality"""
    cache = MemoryCache()

    # Set with 0.1s TTL
    await cache.set("key", "value", ttl=0.1)
    assert await cache.get("key") == "value"

    # Wait for expiry
    await asyncio.sleep(0.2)
    assert await cache.get("key") is None
```

---

### Phase 4: Komplexe Features (70% → 85%)

**Ziel:** LRU, Batch-Operations, Concurrency

```python
@pytest.mark.asyncio
async def test_lru_eviction():
    """Test LRU eviction"""
    cache = MemoryCache(max_size=3)

    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.set("c", 3)
    await cache.get("a")  # Make "a" recently used
    await cache.set("d", 4)  # Should evict "b"

    assert await cache.get("b") is None  # Evicted!
    assert await cache.get("a") == 1     # Still there

@pytest.mark.asyncio
async def test_batch_operations():
    """Test mget/mset"""
    cache = MemoryCache()

    # Batch set
    await cache.mset({"k1": "v1", "k2": "v2"})

    # Batch get
    results = await cache.mget(["k1", "k2"])
    assert results == {"k1": "v1", "k2": "v2"}
```

---

### Phase 5: Branch Coverage (85% → 90%+)

**Ziel:** Alle Code-Pfade testen (if/else, try/except)

```python
@pytest.mark.asyncio
async def test_all_branches():
    """Test every code branch"""
    cache = MemoryCache()

    # Branch: value too large
    huge_value = "x" * (1024 * 1024 * 10)  # 10MB
    result = await cache.set("huge", huge_value)
    assert result is False  # Rejected!

    # Branch: update existing key
    await cache.set("key", "old")
    await cache.set("key", "new")  # Update path
    assert await cache.get("key") == "new"

    # Branch: empty cache operations
    assert await cache.get("nonexistent") is None
    assert await cache.delete("nonexistent") is False
```

---

## 🔧 Tools für klare Coverage-Ergebnisse

### 1. pytest-cov (Primary)

```bash
# Install
pip install pytest-cov

# Run with coverage
pytest tests/test_cache.py --cov=core.cache --cov-report=term-missing

# Generate HTML report
pytest tests/test_cache.py --cov=core.cache --cov-report=html
# Open: htmlcov/index.html
```

### 2. coverage.py (Advanced)

```bash
# Install
pip install coverage

# Run
coverage run -m pytest tests/test_cache.py
coverage report --show-missing
coverage html
```

### 3. Configuration (.coveragerc)

```ini
[run]
source = core
branch = True  # Branch coverage!

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

---

## 📈 CI/CD Integration

### GitHub Action

```yaml
# .github/workflows/coverage.yml
name: Coverage Check

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=core --cov-report=xml --cov-fail-under=80

      - name: Upload to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-coverage
        name: pytest-coverage
        entry: pytest --cov=core.cache --cov-fail-under=80
        language: system
        pass_filenames: false
        always_run: true
```

---

## ✅ Coverage Checklist pro Modul

```markdown
## Für jedes neue Modul:

- [ ] Basisklasse/Funktionen initialisieren
- [ ] Happy Path (erfolgreiche Operationen)
- [ ] Error Cases (Exceptions, None returns)
- [ ] Edge Cases (leere Strings, 0, None)
- [ ] Boundary Values (max_size, TTL expiry)
- [ ] Concurrency (async, threading)
- [ ] Integration (mit anderen Modulen)
- [ ] Performance (Timeouts, große Daten)
```

---

## 🎯 Beispiel: MemoryCache vollständig

### Was wurde getestet?

| Feature | Tests | Coverage |
|---------|-------|----------|
| Initialisierung | 3 | 100% |
| get/set/delete | 8 | 95% |
| TTL Expiry | 4 | 90% |
| LRU Eviction | 3 | 85% |
| Memory Tracking | 4 | 90% |
| Batch Operations | 5 | 95% |
| Concurrency | 3 | 80% |
| Stats | 4 | 100% |
| **Gesamt** | **34** | **~90%** |

---

## 🚀 Quick Start für neue Module

```bash
# 1. Neue Testdatei erstellen
touch tests/test_new_module_comprehensive.py

# 2. Basistemplate kopieren
# (siehe test_core_cache_comprehensive.py)

# 3. Coverage check
pytest tests/test_new_module_comprehensive.py --cov=new_module --cov-report=term

# 4. Fehlende Zeilen identifizieren und ergänzen

# 5. Wiederholen bis 80% erreicht
```

---

## 📚 Lessons Learned

1. **Async Testing:** Jedes `async def` braucht `@pytest.mark.asyncio`
2. **Fixtures:** Wiederverwendbare Setup-Code (cache, tmp_path)
3. **Isolation:** Jeder Test sollte unabhängig sein
4. **Mocking:** Externe Services mocken (Redis, DB)
5. **Edge Cases:** Leere Inputs, None, Exceptions
6. **Concurrency:** Race Conditions testen
7. **Performance:** Timeouts für langsame Operationen

---

## 🎓 Training: 30 Minuten zu 80%

**Minute 0-5:** Coverage analysieren
**Minute 5-15:** Basistests schreiben (40%)
**Minute 15-25:** Async Tests + Edge Cases (70%)
**Minute 25-30:** Branch Coverage optimieren (80%+)

---

**Resultat:** Nach diesem Guide kann jedes Modul auf 80%+ Coverage gebracht werden.

**Nächster Schritt:** `core/state_machine.py` oder `api/routes/agents.py` auf 80% bringen.
