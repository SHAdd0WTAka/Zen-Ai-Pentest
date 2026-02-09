# Subagent Aufgaben-Übersicht

## P0 - Kritische Sicherheits-Fixes

### Subagent: Security-Fix-Agent
**Aufgabe:** Kritische Sicherheitslücken beheben

**Zu erledigen:**
1. Fix Command Injection in `autonomous/tool_executor.py`
   - `subprocess_shell` → `subprocess_exec` mit Argument-Liste
   - Input-Sanitierung hinzufügen
   
2. Fix Variable Bug in `agents/react_agent_vm.py`
   - Zeile mit `config.vm_username` finden und fixen
   - Sollte `self.vm_config.vm_username` sein

3. Hardcoded Credentials entfernen
   - `api/auth.py`: Default-Credentials entfernen
   - `api/core/auth.py`: JWT secret fallback entfernen

4. SSL Verification fixen
   - Alle `verify=False` finden
   - Zertifikats-Handling verbessern

**Output:** PR mit Security-Fixes

---

### Subagent: Version-Consistency-Agent
**Aufgabe:** Versions-Inkonsistenzen beheben

**Zu erledigen:**
1. Alle Versionen auf 2.3.9 standardisieren:
   - `setup.py`: 2.3.7 → 2.3.9
   - `README.md`: 2.3.7 → 2.3.9
   - `zen_ai_pentest.py`: Prüfen und fixen

2. Alle Badges in README aktualisieren

3. CHANGELOG.md prüfen und ggf. ergänzen

**Output:** PR mit Version-Fixes

---

### Subagent: Nmap-Integration-Agent
**Aufgabe:** Fehlende nmap_integration.py erstellen

**Zu erledigen:**
1. `tools/nmap_integration.py` erstellen
   - Ähnliche Struktur wie `masscan_integration.py`
   - Nmap Wrapper mit XML-Parsing
   - Service-Detection
   - OS-Detection
   - Script-Scanning Support

2. Tests in `tests/test_nmap_integration.py` erstellen

3. Tool Registry aktualisieren

**Output:** PR mit Nmap Integration

---

## P1 - Hohe Priorität

### Subagent: Test-Coverage-Agent
**Aufgabe:** Test-Abdeckung erhöhen auf 80%

**Zu erledigen:**
1. Fehlende Tests für Core-Module:
   - `core/orchestrator.py`
   - `core/plugin_manager.py`
   - `core/cache.py`

2. API Endpoint Tests erweitern

3. Integration Tests für Tool-Ausführung

4. Mock-Framework für externe Tools

**Output:** PR mit erweiterten Tests

---

### Subagent: Documentation-Agent
**Aufgabe:** Dokumentation konsolidieren und verbessern

**Zu erledigen:**
1. Duplikate entfernen:
   - `docs/API.md` vs `docs/API_DOCUMENTATION.md`
   - Multiple ROADMAP-Dateien

2. Cloud Deployment Guides erstellen:
   - AWS Deployment
   - Azure Deployment
   - GCP Deployment

3. API Examples erweitern

4. Troubleshooting Guide erstellen

**Output:** PR mit Doc-Updates

---

### Subagent: Workflow-Cleanup-Agent
**Aufgabe:** GitHub Actions Workflows bereinigen

**Zu erledigen:**
1. Duplikate konsolidieren:
   - `ci.yml` vs `python-app.yml`
   - `benchmark.yml` vs `benchmarks.yml`

2. Disabled Workflows fixen oder entfernen:
   - `apply-branch-protection.yml.disabled`
   - `notifications.yml.disabled`
   - etc.

3. Workflow-Dokumentation erstellen

4. Secrets-Dokumentation vervollständigen

**Output:** PR mit Workflow-Cleanup

---

## P2 - Mittlere Priorität

### Subagent: New-Tools-Agent
**Aufgabe:** Neue Sicherheitstools integrieren

**Zu erledigen:**
1. OWASP ZAP Integration
2. Nessus/OpenVAS Integration
3. TruffleHog (Secrets Scanning)
4. ScoutSuite (Cloud Security)
5. Trivy (Container Scanning)

**Output:** PR mit neuen Tool-Integrationen

---

### Subagent: Performance-Agent
**Aufgabe:** Performance-Optimierungen

**Zu erledigen:**
1. Async-Optimierungen in Tool-Execution
2. Caching-Strategien verbessern
3. Datenbank-Query-Optimierung
4. Memory-Management verbessern

**Output:** PR mit Performance-Optimierungen

---

### Subagent: Helm-Chart-Agent
**Aufgabe:** Kubernetes Helm Chart erstellen

**Zu erledigen:**
1. Helm Chart Struktur erstellen
2. Values.yaml mit Konfiguration
3. Templates für alle Komponenten
4. Dependencies (PostgreSQL, Redis)
5. Documentation

**Output:** PR mit Helm Chart

---

## Status-Tracking

| Subagent | Status | Assignee | PR |
|----------|--------|----------|-----|
| Security-Fix-Agent | 🔴 Pending | - | - |
| Version-Consistency-Agent | 🔴 Pending | - | - |
| Nmap-Integration-Agent | 🔴 Pending | - | - |
| Test-Coverage-Agent | 🔴 Pending | - | - |
| Documentation-Agent | 🔴 Pending | - | - |
| Workflow-Cleanup-Agent | 🔴 Pending | - | - |
| New-Tools-Agent | 🔴 Pending | - | - |
| Performance-Agent | 🔴 Pending | - | - |
| Helm-Chart-Agent | 🔴 Pending | - | - |

Legende:
- 🔴 Pending
- 🟡 In Progress
- 🟢 Done
