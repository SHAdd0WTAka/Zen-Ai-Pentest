#!/usr/bin/env python3
"""
Kimi Onboard Script - Quick Start fuer neue Kimi Instanzen
"""

import subprocess
from pathlib import Path


def run_git_command(cmd):
    try:
        result = subprocess.run(
            cmd,
            shell=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout.strip() if result.returncode == 0 else "N/A"
    except Exception:
        return "N/A"


def main():
    print("=" * 70)
    print("  ZEN-AI-PENTEST - KIMI ONBOARDING")
    print("=" * 70)
    print()

    stats = {
        "version": "2.3.9",
        "branch": run_git_command("git branch --show-current"),
        "last_commit": run_git_command("git log -1 --pretty=format:%h")[:60],
        "last_commit_date": run_git_command("git log -1 --pretty=format:%cr"),
        "uncommitted": run_git_command("git status --short"),
    }

    print("REPO STATUS")
    print("-" * 70)
    print(f"  Version:      {stats['version']}")
    print(f"  Branch:       {stats['branch']}")
    print(f"  Last Commit:  {stats['last_commit']}")
    print(f"  Committed:    {stats['last_commit_date']}")
    print()

    print("INTEGRATIONS")
    print("-" * 70)
    print("  Telegram:     ON (@Zenaipenbot)")
    print("  Discord:      ON (11 Channels)")
    print("  ISO 27001:    85% Compliance")
    print()

    print("STATISTICS")
    print("-" * 70)
    print("  Workflows:    56")
    print("  Tests:        97")
    print("  Docs:         60+")
    print()

    if stats["uncommitted"]:
        print("ACHTUNG: Uncommitted Changes!")
        print("-" * 70)
        print(stats["uncommitted"])
        print()

    print("OFFENE TASKS")
    print("-" * 70)
    print("  [ ] Discord Channels fuellen")
    print("      -> Workflow: admin-tasks.yml -> fill-discord-channels")
    print()
    print("  [ ] ISO 27001 finalisieren (15% fehlt)")
    print("      -> docs/compliance/")
    print()
    print("  [ ] Test Coverage erhoehen")
    print("      -> tests/ (aktuell ~75%)")
    print()

    print("QUICK ACTIONS")
    print("-" * 70)
    print("  1. Discord Channels fuellen:")
    print("     GitHub Actions -> admin-tasks -> Run workflow")
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

    print("WICHTIGE DATEIEN")
    print("-" * 70)
    print("  SESSION_BACKUP_2026-02-13.md  - Diese Session")
    print("  PROJECT_STATUS_COMPLETE.md    - Vollstaendige Analyse")
    print("  docs/BUG_BOUNTY_PROGRAM.md    - Bug Bounty Details")
    print("  docs/status/repo_status_card.png - Visueller Status")
    print("  AGENTS.md                     - Projekt-Guide")
    print()

    print("SECURITY REMINDER")
    print("-" * 70)
    print("  - Tokens niemals im Chat exposen")
    print("  - GitHub Environments fuer Secrets nutzen")
    print("  - Pre-commit hooks laufen lassen")
    print("  - Dependabot Alerts regelmaessig checken")
    print()

    print("=" * 70)
    print("  Bereit! Frage den User: 'Was sollen wir als naechstes machen?'")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
