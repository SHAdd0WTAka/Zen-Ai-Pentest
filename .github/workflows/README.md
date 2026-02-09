# GitHub Actions Workflows

This directory contains all GitHub Actions workflows for the Zen AI Pentest project.

## Workflow Overview

| Workflow | File | Purpose | Trigger |
|----------|------|---------|---------|
| **CI/CD Pipeline** | `ci.yml` | Main CI pipeline - tests, lint, build | Push/PR to main/master/develop |
| **Security Scan** | `security.yml` | Security analysis (Bandit, Safety, CodeQL, Secrets) | Daily schedule, push/PR |
| **Benchmarks** | `benchmark.yml` | Performance benchmarking | Weekly, PRs to perf-critical code |
| **Release** | `release.yml` | Full release workflow (GitHub, PyPI, Docker) | Tags starting with 'v' |
| **Release Drafter** | `release-drafter.yml` | Auto-generate release drafts | Push to main/master |
| **CodeQL** | `codeql.yml` | Advanced code analysis | Push/PR, weekly schedule |
| **Dependency Review** | `dependency-review.yml` | PR dependency analysis | Pull requests |
| **Coverage** | `coverage.yml` | Code coverage reporting | Push to main/master |
| **Docker** | `docker.yml` | Docker image build/push | Push to main, releases |
| **Pages** | `pages.yml` | Deploy documentation to GitHub Pages | Push to main |
| **Stale** | `stale.yml` | Mark and close stale issues/PRs | Daily schedule |
| **Welcome** | `welcome.yml` | Welcome new contributors | PR opened |
| **Auto Assign** | `auto-assign.yml` | Auto-assign PRs and issues | PR/issue opened |

## Workflow Categories

### CI/CD Workflows
- **`ci.yml`** - Main continuous integration pipeline
  - Backend tests (Python 3.11, 3.12, 3.13)
  - Frontend build test (Node.js 20)
  - Pre-commit hooks validation
  - Database migration checks
  - Docker build test
  - Package build test

### Security Workflows
- **`security.yml`** - Comprehensive security scanning
  - Bandit (Python security linter)
  - Safety (dependency vulnerabilities)
  - pip-audit (package vulnerability scanner)
  - GitLeaks (secret detection)
  - TruffleHog (secret scanning)
  - CodeQL analysis

- **`codeql.yml`** - GitHub CodeQL analysis
- **`dependency-review.yml`** - PR dependency change review

### Release Workflows
- **`release.yml`** - Full release automation
  - GitHub release creation
  - PyPI package publishing (trusted publishing)
  - Docker image build and push (ghcr.io)
  - Documentation deployment
  - Post-release tasks

- **`release-drafter.yml`** - Auto-generate release drafts from merged PRs

### Quality Workflows
- **`coverage.yml`** - Code coverage reporting to Codecov
- **`benchmark.yml`** - Performance regression detection
- **`code-quality.yml`** - Additional code quality checks

### Automation Workflows
- **`auto-assign.yml`** - Auto-assign PRs and issues
- **`stale.yml`** - Manage stale issues/PRs
- **`welcome.yml`** - Welcome first-time contributors
- **`dependabot-auto-merge.yml`** - Auto-merge Dependabot PRs (patch/minor)
- **`auto-merge-dependabot.yml`** - Manual Dependabot merge helper

### Utility Workflows
- **`docker.yml`** - Docker image publishing
- **`pages.yml`** - GitHub Pages deployment
- **`health-check.yml`** - Repository health monitoring
- **`cve-update.yml`** - CVE database updates

### Notification Workflows
- **`telegram-notifications.yml`** - Telegram notifications (manual only)
- **`test-notifications.yml`** - Test notification channels
- **`webhook-notify.yml`** - Generic webhook notifications

## Workflow Dependencies

```
release.yml
├── Requires: ci.yml (tests must pass)
├── Publishes to: GitHub Releases, PyPI, Docker Hub
└── Triggers: pages.yml (docs deployment)

security.yml
├── Runs independently
├── Uploads to: GitHub Security tab
└── Creates: Security alert issues (on scheduled runs)

benchmark.yml
├── Runs on: PRs to performance-critical paths
├── Compares: Current vs baseline performance
└── Comments: Results on PR
```

## Concurrency Configuration

All workflows use concurrency groups to prevent duplicate runs:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Special case for `release.yml`:
```yaml
concurrency:
  group: release
  cancel-in-progress: false  # Never cancel a release
```

## Required Secrets

See [SECRETS.md](./SECRETS.md) for detailed information about required secrets.

### Critical Secrets (Required for full functionality)
- `CODECOV_TOKEN` - Code coverage reporting
- `GITHUB_TOKEN` - Provided automatically, used for releases/issues

### Optional Secrets
- `SLACK_WEBHOOK_URL` - Slack notifications
- `DISCORD_WEBHOOK_URL` - Discord notifications
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` - Telegram notifications
- `OPENROUTER_API_KEY` - For benchmark tests requiring AI

## Timeout Configuration

All jobs have explicit timeouts to prevent hanging:

| Job Type | Timeout |
|----------|---------|
| Quick checks (lint, format) | 10 minutes |
| Tests | 15-30 minutes |
| Security scans | 15-30 minutes |
| Docker builds | 20-30 minutes |
| Releases | 15-30 minutes per job |
| Benchmarks | 60 minutes |

## Adding New Workflows

When adding a new workflow:

1. **Use consistent naming**: `category-purpose.yml` (e.g., `test-integration.yml`)
2. **Add timeout-minutes** to all jobs
3. **Configure concurrency** to prevent duplicate runs
4. **Use latest action versions** (check with `uses: actions/checkout@v4`)
5. **Add to this README** in the appropriate section
6. **Document required secrets** in SECRETS.md

## Workflow Maintenance

### Monthly Tasks
- [ ] Review workflow run history for failures
- [ ] Update action versions if needed
- [ ] Check for deprecated actions (Node 16 warnings)

### Quarterly Tasks
- [ ] Review and optimize workflow run times
- [ ] Evaluate new GitHub Actions features
- [ ] Update timeout values based on actual run times

## Troubleshooting

### Common Issues

**Workflow not triggering:**
- Check the `on:` configuration matches your event
- Verify branch filters include your target branch
- Check if path filters are excluding your changes

**Job hanging:**
- Check if timeout-minutes is set appropriately
- Look for interactive prompts or waiting for input
- Check network connectivity issues

**Permission errors:**
- Verify `permissions:` block in workflow
- Check repository Settings → Actions → General → Workflow permissions
- For releases, ensure `id-token: write` for trusted publishing

### Debug Mode

Add to any job for debugging:
```yaml
- name: Debug Environment
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "Actor: ${{ github.actor }}"
    env | sort
```

## Migration Notes

### Consolidated Workflows (2024)
- `python-app.yml` → merged into `ci.yml`
- `benchmarks.yml` → deleted (duplicate of `benchmark.yml`)
- `security-scan.yml` → deleted (duplicate of `security.yml`)
- `.disabled` workflows → evaluated and removed
