#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Updates the SESSION_STATE.md file with current session information.
.DESCRIPTION
    Automatically captures current git status, recent commits, and environment state
    to create a recovery point for the next Kimi session.
.EXAMPLE
    .\update-session.ps1
    Updates the session state backup file.
#>

$ErrorActionPreference = "Stop"

Write-Host "Updating Kimi Session State Backup..." -ForegroundColor Blue
Write-Host ""

# Get current timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$timestampISO = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"

# Get git information
try {
    $branch = git branch --show-current 2>$null
    $lastCommit = git log -1 --pretty=format:"%h - %s (%ar)" 2>$null
    $recentCommits = git log --oneline -5 2>$null
    $gitStatus = git status --short 2>$null
    $hasChanges = if ($gitStatus) { $true } else { $false }
} catch {
    Write-Warning "Git commands failed. Are you in a git repository?"
    $branch = "unknown"
    $lastCommit = "unknown"
    $recentCommits = "unknown"
    $hasChanges = $false
}

# Get working directory
$workingDir = Get-Location

# Generate new session state content
$content = @"
# Kimi Session State Backup

> **Auto-generated**: $timestamp CET  
> **Session ID**: zen-pentest-$(Get-Date -Format "yyyy-MM-dd")  
> **Branch**: $branch

---

## Current Session Status

### Session Health
| Metric | Status |
|--------|--------|
| Git Status | $(if ($hasChanges) { "⚠️ Uncommitted changes" } else { "✅ Clean" }) |
| Active Branch | $branch |
| Uncommitted Changes | $(if ($hasChanges) { "Yes" } else { "None" }) |
| Last Update | $timestamp |

### Last Action
```
$lastCommit
```

### Recent Commits
```
$recentCommits
```

---

## Active Tasks / Work Queue

### Priority 1: URGENT (Next Actions)
- [ ] **Fix test collection errors** - 3 errors blocking test execution
  - SECRET_KEY environment variable not set
  - ImportError in test_react_agent.py
  - FastAPI parameter assertion error

### Priority 2: IN PROGRESS  
- [x] **ISO 27001 Documentation** - COMPLETED
  - [x] Information Security Policy
  - [x] Statement of Applicability
  - [x] Risk Management Procedure
  - [x] ISMS README

- [x] **Discord Integration** - COMPLETED
  - [x] Server setup (50+ channels, 10 roles)
  - [x] GitHub webhook notifications workflow
  - [x] Token regenerated after exposure

### Priority 3: PENDING / BACKLOG
- [ ] **RDP Configuration** - Decide: disable completely OR configure properly
- [ ] **Discord Permissions** - Manual UI setup for category-specific roles
- [ ] **Security Alerts** - GitHub shows 2 vulnerabilities (1 high, 1 low)
- [ ] **Test Suite** - Fix imports then run full test suite

---

## Technical Context

### Environment
```
OS: Windows 11
Python: 3.13
Shell: PowerShell 7.5.4
Working Dir: $workingDir
Git Branch: $branch
```

### Required Environment Variables (for tests)
```
SECRET_KEY: <NOT SET> - MUST be 32+ characters
DATABASE_URL: Optional (defaults to SQLite)
DISCORD_WEBHOOK_URL: Set in GitHub Secrets
TELEGRAM_BOT_TOKEN: Set in GitHub Secrets
CODECOV_TOKEN: Set in GitHub Secrets
```

---

## Project Knowledge

### Key Files (Recently Modified)
```
docs/compliance/iso27001/
├── README.md                          # ISMS overview
├── information-security-policy.md     # POL-001
├── risk-management-procedure.md       # Risk assessment
└── statement-of-applicability.md      # 93 controls mapped

.github/workflows/
├── discord-github-notify.yml          # Discord integration
├── coverage.yml                       # Fixed
└── telegram-notifications.yml         # Fixed
```

### Compliance Status
- ISO 27001: 85% applicable controls documented
- No Telemetry: Core privacy principle implemented
- MIT License: Open source compliance

---

## Recovery Instructions for Next Kimi

### Step 1: Verify Environment
```powershell
cd $workingDir
git status
git log --oneline -3
```

### Step 2: Check Active Branch
```powershell
git branch --show-current
# Should be: $branch
```

### Step 3: Load Context
Read these files in order:
1. SESSION_STATE.md (this file) - Current status
2. AGENTS.md - Project structure and guidelines
3. docs/compliance/iso27001/README.md - ISMS status

### Step 4: Continue Work
Current priority:
1. Fix test collection errors (set SECRET_KEY, fix imports)
2. Address Dependabot security alerts
3. Run full test suite

---

## Session Log

| Time | Action | Status |
|------|--------|--------|
| 18:24 | Started session | Context loaded |
| 18:30 | Fixed coverage workflow | PR #99 merged |
| 19:00 | Fixed Telegram notifications | PR #100 merged |
| 19:30 | Set up Discord server | 50+ channels created |
| 20:00 | Created Discord webhook workflow | PR #101 created |
| 20:30 | Investigated USB error | Hardware issue (resolved) |
| 21:00 | Investigated msrdc.exe | Confirmed benign (WSL-GUI) |
| 21:30 | Created ISO 27001 docs | 4 documents committed |

---

## Quick Links

| Resource | URL/Path |
|----------|----------|
| GitHub Repo | https://github.com/SHAdd0WTAka/Zen-Ai-Pentest |
| Security Alerts | https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/security/dependabot |
| Active Branch | $branch |
| Discord Server | Zen-Ai (configured) |

---

## Backup Metadata

```
backup_version: 1.0
last_update: $timestampISO
session_owner: @SHAdd0WTAka
auto_update_script: .\update-session.ps1
```

---

**For the next Kimi**: Diese Session hat die ISO 27001 Compliance-Dokumentation erstellt. Die naechsten Schritte sind:
1. Test-Fehler beheben (SECRET_KEY setzen, Imports fixen)
2. Dependabot Security Alerts pruefen
3. Test-Suite laufen lassen

Wenn du frisch startest, lies zuerst diese Datei, dann AGENTS.md.
"@

# Write to file
$sessionFile = Join-Path $workingDir "SESSION_STATE.md"
$content | Out-File -FilePath $sessionFile -Encoding UTF8

Write-Host "Session state updated successfully!" -ForegroundColor Green
Write-Host "File: $sessionFile" -ForegroundColor Blue
Write-Host "Tip: Run this script after each major task to keep the backup current." -ForegroundColor Yellow

# Also show current git status briefly
Write-Host ""
Write-Host "Current Git Status:" -ForegroundColor Blue
if ($hasChanges) {
    Write-Host "⚠️ You have uncommitted changes:" -ForegroundColor Yellow
    git status --short
} else {
    Write-Host "✅ Working directory clean" -ForegroundColor Green
}
