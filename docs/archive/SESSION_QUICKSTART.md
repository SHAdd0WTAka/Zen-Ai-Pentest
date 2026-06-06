# ⚡ Kimi Quickstart - Emergency Recovery

> **If you just loaded into this project, read this first!**

---

## 🎯 What to Do RIGHT NOW

### 1. Check Environment (30 seconds)
```powershell
cd C:\Users\Ataka\zen-ai-pentest-test
git status
git branch --show-current
```

### 2. Read This Status (2 minutes)
| Item | Status | Action Needed |
|------|--------|---------------|
| Git Branch | feature/discord-github-integration | ✅ OK |
| Uncommitted Changes | None | ✅ OK |
| Test Suite | Broken (3 errors) | ⚠️ FIX NEXT |
| Security Alerts | 2 alerts (1 high) | ⚠️ REVIEW |

### 3. Your Mission (Pick ONE)

**Option A: Fix Tests** (Recommended)
```powershell
# Set required env var
$env:SECRET_KEY = "your-32-char-secret-key-here-change-in-production"

# Try collecting tests
pytest --collect-only

# Fix any import errors, then run
pytest -v
```

**Option B: Review Security**
```powershell
# Open in browser
start https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/dependabot
```

---

## 📂 Key Files You MUST Know

| File | Why Important |
|------|---------------|
| `SESSION_STATE.md` | Full session backup with all details |
| `AGENTS.md` | Project structure and coding guidelines |
| `docs/compliance/iso27001/README.md` | ISMS compliance status |

---

## 🚨 Critical Context

### Recent Major Work (Last Session)
- ✅ ISO 27001 compliance docs created (4 files)
- ✅ Discord integration complete (50+ channels)
- ✅ Coverage workflow fixed
- ✅ Telegram notifications fixed

### Current Blockers
1. **Tests fail** - Need SECRET_KEY env var
2. **2 Dependabot alerts** - Need dependency updates
3. **RDP unclear** - Either disable or configure properly

### Environment Variables Needed
```powershell
$env:SECRET_KEY = "minimum-32-characters-long-secret-key-here"
$env:DATABASE_URL = "optional-postgresql-or-sqlite-default"
```

---

## 💡 Quick Commands

```powershell
# Update session backup
.\update-session.ps1

# Run tests (after fixing SECRET_KEY)
pytest --cov=api,agents,core -v

# Check security
bandit -r . -ll
safety check -r requirements.txt

# Git workflow
git add .
git commit -m "type: description"
git push origin feature/discord-github-integration
```

---

## 🆘 Help

Stuck? Check these in order:
1. `SESSION_STATE.md` - Full context
2. `AGENTS.md` - Project guide
3. GitHub Issues - https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues

---

**Last Updated**: 2026-02-11 21:30 CET
**Session**: zen-pentest-2026-02-11
**Owner**: @SHAdd0WTAka
