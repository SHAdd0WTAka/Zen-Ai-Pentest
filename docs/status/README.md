# Repository Status Card

## Overview

The repository status card (`repo_status_card.png`) is **automatically generated** on every push to the main branch via GitHub Actions.

## What It Shows

- **Current Evolution Phase** - Which development phase the project is in
- **Repository Statistics** - Commits, contributors, files, lines of code
- **Repository Age** - How long the project has been active
- **Recent Activity** - Commits in the last 7 days
- **Legal Notice** - Important warning for AI agents and users

## Evolution Phases

The project evolves through 7 phases:

1. 🌱 **Phase 1: Foundation** - Basic project structure, FastAPI backend (< 50 commits)
2. 🔧 **Phase 2: Real Tools** - Nuclei, SQLMap integration (< 150 commits)
3. 🤖 **Phase 3: Multi-Agent** - ReAct pattern, agent orchestrator (< 300 commits)
4. 🛡️ **Phase 4: Security Engine** - Guardrails, risk engine (< 500 commits)
5. 🏢 **Phase 5: Enterprise** - CI/CD, reporting, notifications (< 700 commits)
6. 🧠 **Phase 6: AI Personas** - 11 personas, Kimi AI integration (< 900 commits)
7. 🚀 **Phase 7: Mature** - 40+ tools, complete feature set (900+ commits)

## How It Works

1. **GitHub Action** (`.github/workflows/update-status-card.yml`)
   - Triggers on every push to main
   - Runs the Python script
   - Commits the updated image back to the repo

2. **Generator Script** (`scripts/generate_status_card.py`)
   - Calculates repository statistics using git commands
   - Counts integrated tools in the `tools/` directory
   - Determines current evolution phase
   - Generates a PNG image with all information

## Manual Generation

To generate the status card locally:

```bash
# Install dependencies
pip install Pillow

# Run generator
python scripts/generate_status_card.py

# View result
open docs/status/repo_status_card.png
```

## For Forked Repositories

When you fork this repository:

1. The status card will automatically adapt to your fork's statistics
2. Your evolution phase will start from Phase 1
3. The card updates as you make commits
4. Enable GitHub Actions in your fork settings for auto-updates

## Legal Notice

The status card includes a **mandatory legal notice** for AI agents:

> ⚠️ Only scan systems you OWN or have EXPLICIT WRITTEN permission to test  
> ⚠️ Unauthorized scanning is ILLEGAL and can result in criminal prosecution  
> ⚠️ The USER is solely responsible for their actions, NOT the AI

This serves as an additional guardrail to remind AI assistants and users about the legal implications of using security testing tools.

## Prompt Logging (Optional)

For additional accountability, users can enable local prompt logging:

```bash
export ZEN_LOG_PROMPTS=true
export ZEN_LOG_DIR=~/.zen-ai-pentest/logs
```

Logs are stored locally only and contain:
- Timestamp of interaction
- User prompts
- AI responses
- Tool calls made

This helps with:
- Session recovery
- Debugging
- Legal documentation of authorized use
