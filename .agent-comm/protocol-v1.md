# 🤖 Agent Communication Protocol v1.0

## Rollen:
- **CLI-Kimi** (hier): Reviewer, Strategie, Planung
- **PowerShell-Kimi** (Windows): Executor, Debugger, Worker

## Workflow:

### 1. Screenshot-Share (von Dir/Ataka)
```markdown
## Screenshot Ref
- **Von:** Ataka
- **Zeigt:** GitHub Actions Fehler
- **Pfad:** `C:\Users\Ataka\screenshot_123.png`
- **Zeit:** 2026-02-11 04:20
```

### 2. Analyse (CLI-Kimi)
```markdown
## [CLI-Kimi] → [PowerShell-Kimi]
**Task:** Fix telegram-notifications.yml
**Screenshot zeigt:** Webhook 404 Fehler

**Instructions:**
```powershell
# Gehe zu Workflow
gh run view 123 --log | Select-String "telegram"

# Fix: URL in .github/workflows/telegram-notifications.yml
# Ändere: old-url → new-url

# Dann:
git checkout -b fix/telegram-$(date +%s)
git add .git commit -m "fix: Telegram webhook"
git push origin HEAD
gh pr create --reviewer SHAdd0WTAka
```

**Expected Result:** PR erstellt
```

### 3. Execution (PowerShell-Kimi)
```markdown
## [PowerShell-Kimi] → [CLI-Kimi]
**Status:** ✅ Task complete
**PR:** #101
**Branch:** fix/telegram-20260211
**Ergebnis:** Webhook URL gefixt

**Output:**
```
[gh output hier...]
```

**Needs Review:** Ja
```

### 4. Review (CLI-Kimi)
```markdown
## [CLI-Kimi] → [PowerShell-Kimi]
**Review:** ✅ APPROVED
**Merge:** Auto-merged #101
**Next Task:** Siehe .agent-comm/task-queue.md
```

---

## Schnell-Kommandos:

### Von CLI-Kimi:
```bash
# Neue Aufgabe erstellen
echo "## [CLI-Kimi] → [PowerShell-Kimi]" >> .agent-comm/instructions-$(date +%s).md
```

### Von PowerShell-Kimi:
```powershell
# Status updaten
echo "## [PowerShell-Kimi] → [CLI-Kimi]" >> .agent-comm/response-$(Get-Date -Format 'yyyyMMdd-HHmm').md
```

---

## Automatisierung:

Beide Agenten können:
1. `git pull` machen um neue Nachrichten zu sehen
2. Auf Änderungen in `.agent-comm/` warten
3. Automatisch reagieren

**Emoji Code:**
- 🆕 Neue Aufgabe
- 🔄 In Progress
- ✅ Complete
- ❌ Blocked (braucht Hilfe)
- 📸 Screenshot attached
