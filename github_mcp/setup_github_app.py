#!/usr/bin/env python3
"""
🚀 GitHub App Setup für ZEN-ALPHA MCP
Erstellt automatisch:
- Private Repo
- GitHub Actions Workflows
- Secrets
- Issue Templates
"""

import base64
import json
import os
import sys

import requests


class GitHubAppSetup:
    """Automatisches Setup der GitHub MCP Infrastruktur"""

    def __init__(self, github_token: str, repo_owner: str):
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"

    def create_mcp_repository(self, repo_name: str = "zen-alpha-mcp", private: bool = True) -> dict:
        """Erstelle privates MCP Repository"""
        print(f"📦 Creating repository: {repo_name}...")

        data = {
            "name": repo_name,
            "description": "🔐 ZEN-ALPHA MCP Server - AI Memory, Tasks, Credentials Hub",
            "private": private,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False,
            "auto_init": True,
            "gitignore_template": "Python",
            "license_template": "mit",
        }

        response = requests.post(f"{self.base_url}/user/repos", headers=self.headers, json=data, timeout=30)

        if response.status_code == 201:
            print(f"  ✅ Repository created: {response.json()['html_url']}")
            return response.json()
        elif response.status_code == 422:
            print("  ℹ️  Repository already exists")
            return self.get_repository(repo_name)
        else:
            print(f"  ❌ Error: {response.text}")
            return None

    def get_repository(self, repo_name: str) -> dict:
        """Hole existierendes Repository"""
        response = requests.get(f"{self.base_url}/repos/{self.repo_owner}/{repo_name}", headers=self.headers, timeout=30)
        return response.json() if response.status_code == 200 else None

    def create_directory_structure(self, repo_name: str):
        """Erstelle Verzeichnisstruktur im Repo"""
        print("\n📁 Creating directory structure...")

        files = {
            # README
            "README.md": self._generate_readme(),
            # MCP Config
            ".mcp/config.json": json.dumps(
                {
                    "version": "1.0.0",
                    "name": "ZEN-ALPHA MCP",
                    "description": "AI Memory & Task Hub",
                    "capabilities": [
                        "memory",
                        "tasks",
                        "credentials",
                        "workflows",
                    ],
                    "providers": ["anthropic", "codex", "kimi"],
                },
                indent=2,
            ),
            # GitHub Actions Workflows
            ".github/workflows/ai-task-runner.yml": self._generate_task_workflow(),
            ".github/workflows/cron-memory-cleanup.yml": self._generate_cron_workflow(),
            ".github/workflows/notify-on-task.yml": self._generate_notify_workflow(),
            # Issue Templates
            ".github/ISSUE_TEMPLATE/ai_memory.md": self._generate_memory_template(),
            ".github/ISSUE_TEMPLATE/task.md": self._generate_task_template(),
            ".github/ISSUE_TEMPLATE/credential_request.md": self._generate_credential_template(),
            # Documentation
            "docs/MCP_API.md": self._generate_api_docs(),
            "docs/SECURITY.md": self._generate_security_docs(),
        }

        for path, content in files.items():
            self._create_or_update_file(repo_name, path, content)

    def _create_or_update_file(self, repo_name: str, path: str, content: str):
        """Erstelle oder aktualisiere Datei im Repo"""
        # Prüfe ob Datei existiert
        check_resp = requests.get(
            f"{self.base_url}/repos/{self.repo_owner}/{repo_name}/contents/{path}", headers=self.headers, timeout=30
        )

        encoded_content = content.encode("utf-8")
        import base64

        b64_content = base64.b64encode(encoded_content).decode()

        data = {"message": f"Setup: {path}", "content": b64_content}

        if check_resp.status_code == 200:
            data["sha"] = check_resp.json()["sha"]

        response = requests.put(
            f"{self.base_url}/repos/{self.repo_owner}/{repo_name}/contents/{path}", headers=self.headers, json=data, timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"  ✅ {path}")
        else:
            print(f"  ❌ {path}: {response.status_code}")

    def setup_secrets(self, repo_name: str, secrets: dict):
        """Setup GitHub Secrets"""
        print("\n🔐 Setting up secrets...")

        # Get public key for encryption
        key_resp = requests.get(
            f"{self.base_url}/repos/{self.repo_owner}/{repo_name}/actions/secrets/public-key", headers=self.headers, timeout=30
        )

        if key_resp.status_code != 200:
            print("  ❌ Failed to get public key")
            return

        key_data = key_resp.json()

        for name, value in secrets.items():
            if not value:
                continue

            # Encrypt value
            from nacl import public

            public_key = public.PublicKey(base64.b64decode(key_data["key"]))
            sealed_box = public.SealedBox(public_key)
            encrypted = base64.b64encode(sealed_box.encrypt(value.encode())).decode()

            # Store secret
            resp = requests.put(
                f"{self.base_url}/repos/{self.repo_owner}/{repo_name}/actions/secrets/{name}",
                headers=self.headers,
                json={
                    "encrypted_value": encrypted,
                    "key_id": key_data["key_id"],
                },
                timeout=30,
            )

            if resp.status_code in [201, 204]:
                print(f"  ✅ Secret: {name}")
            else:
                print(f"  ❌ Secret: {name}")

    def create_project_board(self, repo_name: str):
        """Erstelle Project Board für Aufgaben"""
        print("\n📋 Creating project board...")

        # Create project
        response = requests.post(
            f"{self.base_url}/repos/{self.repo_owner}/{repo_name}/projects",
            headers=self.headers,
            json={
                "name": "AI Task Board",
                "body": "Task management for AI agents and workflows",
            },
            timeout=30,
        )

        if response.status_code == 201:
            project = response.json()
            print(f"  ✅ Project created: {project['html_url']}")

            # Create columns
            columns = ["Backlog", "In Progress", "Review", "Done"]
            for col in columns:
                col_resp = requests.post(
                    f"{self.base_url}/projects/{project['id']}/columns", headers=self.headers, json={"name": col}, timeout=30
                )
                if col_resp.status_code == 201:
                    print(f"    ✅ Column: {col}")

    def _generate_readme(self) -> str:
        return """# 🔐 ZEN-ALPHA MCP Server

**Model Context Protocol Server** powered by GitHub

## 🎯 Purpose

Zentraler Hub für:
- 🧠 **AI Memory** - Kontext über Sessions hinweg speichern
- 🎯 **Aufgaben** - Task management für AI Agents
- 🔑 **Credentials** - Sichere API Key Verwaltung
- ⚙️ **Workflows** - Automatisierte Cronjobs & Trigger

## 🚀 Quick Start

### Web Interface
```
https://774236f6.zen-alpha-pentest.pages.dev
```

### API Access
```bash
# Get your GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/zen-alpha-mcp/issues
```

## 📁 Structure

```
zen-alpha-mcp/
├── .github/
│   ├── workflows/          # Automated tasks
│   │   ├── ai-task-runner.yml
│   │   ├── cron-memory-cleanup.yml
│   │   └── notify-on-task.yml
│   └── ISSUE_TEMPLATE/     # Templates
│       ├── ai_memory.md
│       ├── task.md
│       └── credential_request.md
├── .mcp/
│   └── config.json         # MCP Configuration
├── docs/
│   ├── MCP_API.md
│   └── SECURITY.md
└── README.md
```

## 🔐 Security

- **Private Repository** - Nur autorisierte Zugriffe
- **Encrypted Secrets** - API Keys in GitHub Secrets
- **Audit Trail** - Alle Änderungen via Git History
- **No Local Storage** - Alles in der Cloud

## 🤖 AI Providers

Configured providers:
- ✅ Anthropic Claude
- ✅ OpenAI Codex
- ✅ Kimi AI

## 📝 Usage

### Store Memory
```python
from github_mcp import get_mcp_server

mcp = get_mcp_server(github_token="...")
mcp.save_memory(
    session_id="abc123",
    content="Important context...",
    tags=["project-x", "architecture"]
)
```

### Create Task
```python
task = Task(
    id="task_001",
    title="Implement auth",
    assignee="@ai-agent-1",
    priority="high"
)
mcp.create_task(task)
```

### Trigger AI
```python
response = mcp.call_anthropic(
    prompt="Analyze this code...",
    context=mcp.get_memories(tags=["project-x"])
)
```

---

**ZEN-ALPHA** | Made with ❤️ for the AI community
"""

    def _generate_task_workflow(self) -> str:
        return """name: 🤖 AI Task Runner

on:
  issues:
    types: [opened, labeled]
  workflow_dispatch:
    inputs:
      task_id:
        description: 'Task ID to run'
        required: true

jobs:
  process-task:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.labels.*.name, 'task') || github.event_name == 'workflow_dispatch'

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install requests
        pip install pynacl

    - name: Process Task
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        ISSUE_NUMBER: ${{ github.event.issue.number }}
      run: |
        python .github/scripts/process_task.py

    - name: Update Issue
      uses: actions/github-script@v7
      with:
        script: |
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: '✅ Task processed by AI'
          })
"""

    def _generate_cron_workflow(self) -> str:
        return """name: 🧹 Memory Cleanup

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Close Old Memories
      uses: actions/github-script@v7
      with:
        script: |
          const daysOld = 30;
          const cutoff = new Date();
          cutoff.setDate(cutoff.getDate() - daysOld);

          const issues = await github.rest.issues.listForRepo({
            owner: context.repo.owner,
            repo: context.repo.repo,
            state: 'open',
            labels: 'memory'
          });

          for (const issue of issues.data) {
            const created = new Date(issue.created_at);
            if (created < cutoff) {
              await github.rest.issues.update({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                state: 'closed',
                labels: ['memory', 'archived']
              });
              console.log(`Archived #${issue.number}`);
            }
          }
"""

    def _generate_notify_workflow(self) -> str:
        return """name: 🔔 Task Notifications

on:
  issues:
    types: [opened, assigned]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  notify:
    runs-on: ubuntu-latest

    steps:
    - name: Check Overdue Tasks
      uses: actions/github-script@v7
      with:
        script: |
          const issues = await github.rest.issues.listForRepo({
            owner: context.repo.owner,
            repo: context.repo.repo,
            state: 'open',
            labels: 'task'
          });

          const now = new Date();

          for (const issue of issues.data) {
            // Parse due date from body
            const dueMatch = issue.body.match(/\\*\\*Due:\\*\\*(.+)/);
            if (dueMatch) {
              const due = new Date(dueMatch[1].trim());
              if (due < now) {
                // Add overdue label
                await github.rest.issues.addLabels({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issue.number,
                  labels: ['overdue']
                });
              }
            }
          }
"""

    def _generate_memory_template(self) -> str:
        return """---
name: AI Memory
about: Store AI context/memory
title: '🧠 Memory: '
labels: ['memory', 'ai-context']
assignees: ''
---

## Context

**Session ID:** <!-- e.g., session_abc123 -->
**AI Provider:** <!-- anthropic/codex/kimi -->

## Memory Content

<!-- What should be remembered? -->

## Tags

<!-- e.g., project-x, architecture, bug-fix -->

## Related Tasks

<!-- Link related issues #123 -->
"""

    def _generate_task_template(self) -> str:
        return """---
name: Task
about: Create new AI task
title: '🎯 Task: '
labels: ['task', 'pending']
assignees: ''
---

## Task Description

**Assignee:** <!-- @ai-agent-1 or @username -->
**Priority:** <!-- low/medium/high/critical -->
**Due:** <!-- YYYY-MM-DD -->

## Details

<!-- Task description -->

## AI Context

```json
{
  "model": "claude-3-opus",
  "context_refs": ["#123", "#124"],
  "tools": ["code-analysis", "testing"]
}
```

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
"""

    def _generate_credential_template(self) -> str:
        return """---
name: Credential Request
about: Request new API key storage
title: '🔑 Credential: '
labels: ['credential-request']
assignees: ''
---

## Credential Details

**Name:** <!-- e.g., ANTHROPIC_API_KEY -->
**Service:** <!-- e.g., Anthropic, OpenAI -->
**Scope:** <!-- What is this key for? -->

## ⚠️ Security Notice

**DO NOT paste the actual key here!**

After this issue is created:
1. A maintainer will add the secret
2. This issue will be closed
3. Key will be available in workflows

## Requester

<!-- Your GitHub username -->
"""

    def _generate_api_docs(self) -> str:
        return """# MCP API Documentation

## Endpoints

### Memory Management

```python
# Save memory
POST /repos/{owner}/{repo}/issues
{
  "title": "🧠 Memory: ...",
  "body": "...",
  "labels": ["memory"]
}

# Get memories
GET /repos/{owner}/{repo}/issues?labels=memory&state=open
```

### Task Management

```python
# Create task
POST /repos/{owner}/{repo}/issues
{
  "title": "🎯 Task: ...",
  "labels": ["task", "high"]
}

# Update status
PATCH /repos/{owner}/{repo}/issues/{number}
{
  "labels": ["task", "completed"],
  "state": "closed"
}
```

### Workflow Triggers

```python
# Trigger workflow
POST /repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches
{
  "ref": "main",
  "inputs": {
    "task_id": "task_123"
  }
}
```

## Authentication

All requests require:
```
Authorization: token {github_token}
Accept: application/vnd.github.v3+json
```
"""

    def _generate_security_docs(self) -> str:
        return """# Security Policy

## Credentials

- All API keys stored in **GitHub Secrets**
- Encrypted at rest
- Only accessible via GitHub Actions
- Never logged or exposed

## Access Control

- Private repository
- Branch protection rules
- Required reviews for changes

## Audit Trail

- All changes tracked via Git history
- Issues preserve context
- Actions logs all operations

## Reporting

Report security issues via GitHub Security Advisory.
"""


def main():
    """Main setup function"""
    print("🚀 ZEN-ALPHA MCP Server Setup")
    print("=" * 50)

    # Get token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN environment variable required")
        print("   Create one at: https://github.com/settings/tokens")
        sys.exit(1)

    # Get owner
    owner = os.getenv("GITHUB_OWNER", "SHAdd0WTAka")

    # Initialize setup
    setup = GitHubAppSetup(token, owner)

    # Create repo
    repo = setup.create_mcp_repository()
    if not repo:
        print("❌ Failed to create repository")
        sys.exit(1)

    repo_name = repo["name"]

    # Create structure
    setup.create_directory_structure(repo_name)

    # Setup secrets (from env)
    secrets = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "KIMI_API_KEY": os.getenv("KIMI_API_KEY", ""),
    }
    setup.setup_secrets(repo_name, secrets)

    # Create project board
    setup.create_project_board(repo_name)

    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print(f"📦 Repository: {repo['html_url']}")
    print(f"🔐 Private: {repo['private']}")
    print("\nNext steps:")
    print("  1. Clone the repository")
    print("  2. Configure your AI API keys in GitHub Secrets")
    print("  3. Start using the MCP Server!")


if __name__ == "__main__":
    main()
