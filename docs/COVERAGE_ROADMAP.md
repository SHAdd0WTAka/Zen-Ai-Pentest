# 📈 Coverage Roadmap - Von 13% zu 80%

> **Aktueller Stand:** 13% (226 Tests, 12 Failed)
> **Ziel:** 80% Coverage
> **Zeithorizont:** 4-6 Wochen (stufenweise)

---

## 🎯 Meilensteine

```
13% ────► 30% ────► 50% ────► 70% ────► 80%
  │        │         │         │         │
Week 1   Week 2    Week 3    Week 4    Week 5-6
```

| Milestone | Target | Fokus | Status |
|-----------|--------|-------|--------|
| 🚀 **M1** | 30% | Core + Security | 🔴 Geplant |
| 🚀 **M2** | 50% | API + Modules | 🔴 Geplant |
| 🚀 **M3** | 70% | Agents + Tools | 🔴 Geplant |
| 🚀 **M4** | 80% | Edge Cases + Integration | 🔴 Geplant |

---

## 📋 Milestone 1: 13% → 30% (Week 1)

**Ziel:** Kritische Sicherheits- und Kernfunktionen

### Module (Priorität 1 - Kritisch)

| Modul | Aktuell | Ziel | Zeilen | Aufwand |
|-------|---------|------|--------|---------|
| `api/auth.py` | 62% | 90% | 70 | 🟢 Klein |
| `api/csrf_protection.py` | 64% | 90% | 102 | 🟢 Klein |
| `core/database.py` | 65% | 90% | 68 | 🟢 Klein |
| `modules/api_key_manager.py` | 86% | 95% | 210 | 🟢 Klein |
| `modules/risk_scoring.py` | 92% | 95% | 83 | 🟢 Klein |

**Tasks:**
- [ ] Fix 12 failed Tests (bcrypt, jwt installieren)
- [ ] Vervollständige `api/auth.py` Tests
- [ ] CSRF Token Tests erweitern
- [ ] API Key Manager Tests fixen

**Erwartetes Ergebnis:** +17% Coverage

---

## 📋 Milestone 2: 30% → 50% (Week 2)

**Ziel:** API Layer und wichtige Module

### Module (Priorität 2 - Hoch)

| Modul | Aktuell | Ziel | Zeilen | Aufwand |
|-------|---------|------|--------|---------|
| `api/main.py` | 31% | 70% | 478 | 🟡 Mittel |
| `api/rate_limiter_v2.py` | 66% | 85% | 263 | 🟢 Klein |
| `modules/false_positive_filter.py` | 98% | 100% | 62 | 🟢 Klein |
| `modules/agent_coordinator.py` | 77% | 90% | 130 | 🟢 Klein |
| `risk_engine/scorer.py` | 80% | 90% | 115 | 🟢 Klein |

**Tasks:**
- [ ] API Endpoints testen (health, status)
- [ ] Rate Limiter Tests vervollständigen
- [ ] Agent Coordinator Integration Tests
- [ ] Risk Scoring Edge Cases

**Erwartetes Ergebnis:** +20% Coverage

---

## 📋 Milestone 3: 50% → 70% (Week 3-4)

**Ziel:** Agents und Tool-Integrationen

### Module (Priorität 3 - Mittel)

| Modul | Aktuell | Ziel | Zeilen | Aufwand |
|-------|---------|------|--------|---------|
| `autonomous/exploit_validator.py` | 62% | 80% | 479 | 🟡 Mittel |
| `autonomous/react.py` | 76% | 85% | 125 | 🟢 Klein |
| `tools/tool_registry.py` | 72% | 85% | 155 | 🟢 Klein |
| `tools/tool_caller.py` | 72% | 85% | 95 | 🟢 Klein |
| `utils/async_fixes.py` | 48% | 75% | 67 | 🟢 Klein |

**Tasks:**
- [ ] Exploit Validator Unit Tests
- [ ] React Agent Flow Tests
- [ ] Tool Registry Integration
- [ ] Async Utilities testen

**Erwartetes Ergebnis:** +20% Coverage

---

## 📋 Milestone 4: 70% → 80% (Week 5-6)

**Ziel:** Edge Cases, Integration, Rest-Module

### Module (Priorität 4 - Optional)

| Modul | Aktuell | Ziel | Zeilen | Aufwand |
|-------|---------|------|--------|---------|
| `api/routes/` | 0-30% | 60% | ~2000 | 🔴 Groß |
| `core/` (Rest) | 0-65% | 70% | ~1000 | 🟡 Mittel |
| `database/` | 21-71% | 80% | ~300 | 🟢 Klein |
| `monitoring/` | 0% | 50% | ~200 | 🟢 Klein |

**Tasks:**
- [ ] API Routes (auth, scans, findings)
- [ ] Database CRUD Operations
- [ ] Monitoring/Metrics Tests
- [ ] Integration Tests (End-to-End)

**Erwartetes Ergebnis:** +10% Coverage

---

## 🔧 Technische Voraussetzungen

### Dependencies installieren
```bash
pip install bcrypt pyjwt pytest-asyncio
```

### Test-Struktur
```
tests/
├── unit/           # Einzelne Funktionen
├── integration/    # Zusammenspiel
├── security/       # Sicherheitstests
└── e2e/            # End-to-End
```

---

## 📊 Fortschritts-Tracking

| Woche | Ziel | Tatsächlich | Delta |
|-------|------|-------------|-------|
| Week 1 | 30% | ? | - |
| Week 2 | 50% | ? | - |
| Week 3 | 60% | ? | - |
| Week 4 | 70% | ? | - |
| Week 5 | 75% | ? | - |
| Week 6 | 80% | ? | - |

---

## 🎯 Definition of Done

- [ ] Alle kritischen Module (P1) > 80%
- [ ] Keine failed Tests in CI
- [ ] Codecov Badge zeigt 80%+
- [ ] PR Check „Coverage“ ist grün
- [ ] Dokumentation aktualisiert

---

## 💡 Quick Wins (sofort umsetzbar)

1. **Fix failed Tests** → +2-3% Coverage
2. **Add `__init__.py` zu tests_ci** → Sauberere Struktur
3. **Test-Dependencies fixen** → Stabiles CI
4. **Leere Tests für 0% Module** → Basis für später

---

**Erstellt:** $(date)
**Nächstes Review:** Nach Milestone 1
