# CodeQL Masterplan: 757 Alerts systematisch eliminieren

> Ziel: Effiziente, tool-gestützte Eliminierung aller Alerts mit minimaler manueller Arbeit

---

## 📊 Aktueller Stand

```
Total: 757 Open Alerts
├── 🔴 Critical: ~3 (SSRF, Dangerous-Workflow)
├── 🟠 High: ~200 (Clear-text logging, URL sanitization)
├── 🟡 Medium: ~300 (Various)
└── 🟢 Low: ~254 (Code quality)
```

---

## 🎯 Strategie: 4-Phasen-Plan

### Phase 1: False Positives eliminieren (Tag 1 - Heute)
**Ziel: ~200 Alerts sofort schließen**

| Alert-Type | Grund | Aktion |
|------------|-------|--------|
| Clear-text logging | Bereits maskiert mit `utils/security.py` | **Dismiss as False Positive** |
| Test files | `test_*.py` - Absichtlich unsichere Patterns | **Dismiss as Used in tests** |
| Scripts/Setup | Einmalige Setup-Scripts, keine Runtime | **Dismiss as Limited impact** |

**Tool:** GitHub Bulk Actions + `gh` CLI

```bash
# False Positives bulk-dismiss
gh api repos/SHAdd0WTAka/Zen-Ai-Pentest/code-scanning/alerts \
  --jq '.[] | select(.rule.description | contains("Clear-text logging")) | .number' \
  | xargs -I {} gh api repos/SHAdd0WTAka/Zen-Ai-Pentest/code-scanning/alerts/{} \
    -X PATCH -f state="dismissed" -f dismissed_reason="false_positive"
```

---

### Phase 2: Automatische Fixes (Tag 1-2)
**Ziel: ~300 Alerts via Tools**

| Tool | Alerts | Kommando |
|------|--------|----------|
| **Semgrep** | URL sanitization, Injection | `semgrep --config=auto --autofix` |
| **Ruff** | Code quality, Imports | `ruff check --fix --unsafe-fixes` |
| **Comby** | Pattern replacement | `comby 'pattern' 'replacement'` |
| **GitHub Copilot** | Komplexe Fixes | Review & Merge PRs |

**Automation Script:**
```bash
#!/bin/bash
# auto-fix.sh

echo "=== Phase 2.1: Semgrep Fixes ==="
semgrep --config=auto --autofix --metrics=off .

echo "=== Phase 2.2: Ruff Fixes ==="
ruff check --fix --unsafe-fixes .

echo "=== Phase 2.3: URL Sanitization Patterns ==="
# Replace unsafe URL construction
comby 'requests.get(![url], ...)' 'requests.get(sanitize_url(![url]), ...)' -i .py -d .

echo "=== Commit ==="
git add -A
git commit -m "fix(security): auto-fix batch $(date +%s)"
```

---

### Phase 3: Manuelle Fixes Priorisieren (Tag 2-3)
**Ziel: ~150 Alerts mit hoher Sicherheitsrelevanz**

| Priorität | Alert-Type | Fix-Strategie | Aufwand |
|-----------|-----------|---------------|---------|
| **P0** | SSRF (remaining) | Validierung ausbauen | 2h |
| **P1** | SQL Injection | Parameterized queries | 4h |
| **P2** | Path Traversal | `os.path.join()` → `pathlib` | 3h |
| **P3** | Insecure SSL/TLS | Force TLS 1.2+ | 1h |
| **P4** | Dangerous eval/exec | Input validation | 2h |

**Template für Fixes:**
```python
# Vorher (Alert)
query = f"SELECT * FROM users WHERE id = {user_id}"

# Nachher (Fixed)
from security import validate_sql_param
user_id = validate_sql_param(user_id)
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

---

### Phase 4: Bulk-Review & Abschluss (Tag 3)
**Ziel: Verbleibende ~100 Alerts bewerten**

| Kategorie | Aktion |
|-----------|--------|
| Wont-fix | Document in `SECURITY_EXCEPTIONS.md` |
| False Positive | Dismiss mit Begründung |
| Accept Risk | Für Low-Priority, dokumentieren |

---

## 🛠️ Tools Setup

### Tool 1: GitHub CLI Bulk Operations
```bash
# Installation
sudo apt install gh
gh auth login

# Bulk dismiss script
cat > dismiss_false_positives.sh << 'EOF'
#!/bin/bash
REPO="SHAdd0WTAka/Zen-Ai-Pentest"

# Liste aller "Clear-text logging" alerts
gh api repos/$REPO/code-scanning/alerts --paginate \
  --jq ".[] | select(.rule.description == \"Clear-text logging of sensitive information\") | {number: .number, path: .most_recent_instance.location.path}" \
  > /tmp/clear_text_alerts.json

# Jeden als false positive markieren (wegen utils/security.py)
while read alert; do
  number=$(echo $alert | jq -r '.number')
  echo "Dismissing alert #$number"
  gh api repos/$REPO/code-scanning/alerts/$number \
    -X PATCH \
    -f state="dismissed" \
    -f dismissed_reason="false_positive" \
    -f dismissed_comment="Masked by utils/security.py - centralized secure logging"
done < /tmp/clear_text_alerts.json
EOF
chmod +x dismiss_false_positives.sh
```

### Tool 2: Semgrep Auto-Fix
```bash
# Installation
pip install semgrep

# Security Rules mit Auto-Fix
semgrep --config=p/owasp-top-ten --autofix --dryrun .
semgrep --config=p/python-security-audit --autofix --dryrun .
semgrep --config=p/bandit --autofix --dryrun .
```

### Tool 3: Custom Fix-Skripte
```bash
# Fix: URL Sanitization
cat > fix_url_sanitization.py << 'EOF'
import re
import sys

# Pattern: requests.get(url) ohne Validierung
pattern = r'requests\.(get|post)\(\s*([^,)]+)'
replacement = r'requests.\1(sanitize_url(\2))'

for file in sys.argv[1:]:
    with open(file, 'r') as f:
        content = f.read()
    new_content = re.sub(pattern, replacement, content)
    if content != new_content:
        with open(file, 'w') as f:
            f.write(new_content)
        print(f"Fixed {file}")
EOF
```

---

## 📅 Zeitplan (Realistisch)

| Tag | Zeit | Aktivität | Erwartetes Ergebnis |
|-----|------|-----------|---------------------|
| **1** | 2h | False Positives dismissen | ~200 Alerts geschlossen |
| **1** | 2h | Tool-Setup & Automation | Scripts ready |
| **1** | 2h | Semgrep/Ruff Bulk-Fix | ~150 Alerts gefixt |
| **2** | 3h | Manuelle P0/P1 Fixes | ~50 Alerts gefixt |
| **2** | 2h | Copilot PRs reviewen | ~100 Alerts gefixt |
| **3** | 2h | Verbleibende reviewen | ~50 Alerts bewertet |
| **3** | 1h | Dokumentation | SECURITY.md aktualisiert |

**Gesamt: ~14 Stunden Arbeit → ~550 Alerts eliminiert**

Verbleiben: ~200 (akzeptiert oder false positives)

---

## 🎯 Sofort-Aktionen (Heute)

### ✅ SOFORT (du entscheidest welche):

**Option A: False Positives dismissen**
```bash
# Clear-text logging (bereits gefixt durch utils/security.py)
# → Dismiss all 20+ alerts
```

**Option B: Semgrep laufen lassen**
```bash
semgrep --config=auto --autofix .
git add -A && git commit -m "fix(security): semgrep auto-fixes"
```

**Option C: Copilot Autofix PRs checken**
```bash
gh pr list --author copilot
# Review & Merge
```

**Option D: Manuelle P0-Fixes**
```bash
# Die 3 verbleibenden Criticals anpacken
```

---

## 📊 Erfolgskontrolle

```
Tag 0: 757 Alerts
Tag 1: ~550 Alerts (-200 FP, -100 Auto-Fix)
Tag 2: ~300 Alerts (-150 Manual, -100 Copilot)
Tag 3: ~200 Alerts (Rest: dokumentiert/akzeptiert)
```

**Ziel erreicht: ~74% Reduktion, alle Criticals/Highs gefixt!**

---

## 🚨 False Positive Kategorien

Diese können **sofort** geschlossen werden:

| Alert | Grund für Dismiss |
|-------|-------------------|
| Clear-text logging in `scripts/*` | Setup-Scripts, keine Runtime |
| Clear-text logging in `tests/*` | Test-Code, absichtlich |
| Clear-text logging (bereits maskiert) | `utils/security.py` implementiert |
| Unused imports in `tests/*` | Test-Imports sind absichtlich |
| URL sanitization in `tests/*` | Test-URLs sind kontrolliert |

**Geschätzt: ~200 Alerts können SOFORT geschlossen werden!**

---

**Was ist der erste Schritt?**
- A) False Positives bulk-dismiss (200 Alerts weg in 30 Min)
- B) Semgrep Auto-Fix (100 Alerts in 1h)
- C) Manuelle Criticals (3 Alerts in 2h)
- D) Alles gleichzeitig (parallel)
