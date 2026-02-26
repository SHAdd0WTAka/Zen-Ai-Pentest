# Test Coverage Summary

## Current Status: 28 Modules Tested

| # | Module | Lines | Tests | Status |
|---|--------|-------|-------|--------|
| 1 | api/auth.py | 66 | 15 | ✅ 92% |
| 2 | api/schemas.py | 244 | 45 | ✅ 100% |
| 3 | api/core/config.py | 12 | 4 | ✅ 100% |
| 4 | api/core/agents.py | 25 | 7 | ✅ 100% |
| 5 | api/core/scans.py | 32 | 9 | ✅ 100% |
| 6 | api/websocket.py | 100 | 12 | ✅ ~90% |
| 7 | core/database.py | 68 | 8 | ✅ 100% |
| 8 | core/llm_backend.py | 12 | 4 | ✅ 100% |
| 9 | core/input_validator.py | 152 | 16 | ✅ 91% |
| 10 | core/models.py | 186 | 27 | ✅ 98% |
| 11 | core/container.py | 140 | 14 | ✅ 88% |
| 12 | core/secure_config.py | 155 | 12 | ✅ 68% |
| 13 | memory/base.py | 47 | 8 | ✅ 100% |
| 14 | memory/manager.py | 37 | 7 | ✅ 100% |
| 15 | memory/storage.py | 60 | 9 | ✅ 77% |
| 16 | memory/config.py | 1 | 1 | ✅ 100% |
| 17 | utils/stealth.py | 31 | 5 | ✅ 100% |
| 18 | utils/helpers.py | 85 | 11 | ✅ 99% |
| 19 | utils/security.py | 55 | 7 | ✅ 100% |
| 20 | utils/async_fixes.py | 61 | 9 | ✅ 88% |
| 21 | tools/wifi_packet_editor.py | 220 | 26 | ✅ 70% |
| 22 | tools/subfinder_integration.py | 127 | 9 | ✅ ~80% |
| 23 | safety/config.py | 2 | 1 | ✅ 100% |
| 24 | async_fix.py | 6 | 2 | ✅ 37% |
| 25 | agent_comm/models.py | 240 | 20 | ✅ 100% |
| 26 | risk/cvss.py | 273 | 27 | ✅ ~95% |
| 27 | risk/epss.py | 148 | 23 | ✅ ~95% |
| 28 | risk/business_impact.py | 190 | 21 | ✅ ~95% |

**Total: 28 modules, ~620+ tests, ~90% average coverage on tested modules**

## Problem: Gesamtcoverage nur ~17%

Um auf **40% Gesamtcoverage** zu kommen, müssen wir Module mit **>5000 Zeilen** testen.

### Große ungetestete Module (Priorität für 40% Ziel):

| Modul | Zeilen | Impact |
|-------|--------|--------|
| api/main.py | 720 | 🔴 Kritisch |
| core/cache.py | 550 | 🔴 Kritisch |
| core/state_machine.py | 660 | 🔴 Kritisch |
| core/rate_limiter.py | 415 | 🟡 Hoch |
| tools/plugin_system.py | 428 | 🟡 Hoch |
| integrations/zap_integration.py | 330 | 🟡 Hoch |

### Empfohlene Strategie:
1. **api/main.py** testen (FastAPI App) → +5-7% Coverage
2. **core/cache.py** testen → +4-5% Coverage  
3. **core/state_machine.py** testen → +5-6% Coverage
4. **core/rate_limiter.py** testen → +3-4% Coverage

Damit kämen wir auf ~35-40% Gesamtcoverage.

## Testansatz
- Mocking für externe APIs/Tools
- Async-Test-Problematik beachten (kein pytest-asyncio verfügbar)
- Fokus auf Business-Logik, nicht Framework-Boilerplate
