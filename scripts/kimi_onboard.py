#!/usr/bin/env python3
"""
Kimi Onboard Script - Quick Start für neue Kimi Instanzen
Zeigt Status, offene Tasks, und was als nächstes zu tun ist.
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_git_command(cmd):
    """Führt Git Command aus"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        return result.stdout.strip() if result.returncode == 0 else "N/A"
    except:
        return "N/A"

def get_repo_stats():
    """Sammelt Repo-Statistiken"""
    stats = {
        "version": "2.3.9",
        "branch": run_git_command("git branch --show-current"),
        "last_commit": run_git_command("git log -1 --pretty=format:\"%h - %s\"")[:60],
        "last_commit_date": run_git_command("git log -1 --pretty=format:\"%cr\""),
        "uncommitted": run_git_command("git status --short"),
        "workflows": "56",
        "tests": "97",
        "docs": "60+",
        "telegram": "ON",
        "discord": "ON",
        "iso27001": "85%",
    }
    return stats

def print_header():
    print("=" * 70)
    print("  ZEN-AI-PENTEST - KIMI ONBOARDING")
    print("  Quick Start Guide für neue Kimi Instanzen")
    print("=" * 70)
    print()

def print_status(stats):
    print("📊 REPO STATUS")
    print("-" * 70)
    print(f"  Version:      {stats['version']}")
    print(f"  Branch:       {stats['branch']}")
    print(f"  Last Commit:  {stats['last_commit']}")
    print(f"  Committed:    {stats['last_commit_date']}")
    print()
    
    print("🤖 INTEGRATIONS")
    print("-" * 70)
    print(f"  Telegram:     {stats['telegram']} (@Zenaipenbot)")
    print(f"  Discord:      {stats['discord']} (11 Channels)")
    print(f"  ISO 27001:    {stats['iso27001']} Compliance")
    print()
    
    print("📈 STATISTICS")
    print("-" * 70)
    print(f"  Workflows:    {stats['workflows']}")
    print(f"  Tests:        {stats['tests']}")
    print(f"  Docs:         {stats['docs']}")
    print()

def print_open_tasks():
    print("🔄 OFFENE TASKS (Priorisiert)")
    print("-" * 70)
    print("  [ ] Discord Channels füllen")
    print("      → Workflow: admin-tasks.yml → fill-discord-channels")
    print()
    print("  [ ] ISO 27001 finalisieren (15% fehlt)")
    print("      → docs/compliance/")
    print()
    print("  [ ] Test Coverage erhöhen")
    print("      → tests/ (aktuell ~75%)")
    print()

def print_quick_actions():
    print("⚡ QUICK ACTIONS")
    print("-" * 70)
    print("  1. Discord Channels füllen:")
    print("     GitHub Actions → admin-tasks → Run workflow")
    print()
    print("  2. Status Card neu generieren:")
    print("     python scripts/generate_repo_status_card.py")
    print()
    print("  3. Tests laufen lassen:")
    print("     pytest -m 'not slow'")
    print()
    print("  4. API starten:")
    print("     cd api && uvicorn main:app --reload")
    print()

def print_important_files():
    print("📁 WICHTIGE DATEIEN")
    print("-" * 70)
    print("  SESSION_BACKUP_2026-02-13.md  ← Diese Session")
    print("  PROJECT_STATUS_COMPLETE.md    ← Vollständige Analyse")
    print("  docs/BUG_BOUNTY_PROGRAM.md    ← Bug Bounty Details")
    print("  docs/status/repo_status_card.png ← Visueller Status")
    print("  AGENTS.md                     ← Projekt-Guide")
    print()

def print_security_reminder():
    print("🔐 SECURITY REMINDER")
    print("-" * 70)
    print("  • Tokens niemals im Chat exposen")
    print("  • GitHub Environments für Secrets nutzen")
    print("  • Pre-commit hooks laufen lassen")
    print("  • Dependabot Alerts regelmäßig checken")
    print()

def print_footer():
    print("=" * 70)
    print("  Bereit! Frage den User: 'Was sollen wir als nächstes machen?'")
    print("=" * 70)
    print()

def main():
    print_header()
    
    stats = get_repo_stats()
    print_status(stats)
    
    if stats['uncommitted']:
        print("⚠️  ACHTUNG: Uncommitted Changes!")
        print("-" * 70)
        print(stats['uncommitted'])
        print()
    
    print_open_tasks()
    print_quick_actions()
    print_important_files()
    print_security_reminder()
    print_footer()

if __name__ == "__main__":
    main()
