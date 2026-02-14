# Zen-AI-Pentest CI/CD Integration Templates

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/zenai/pentest)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Production-ready CI/CD integration templates for the Zen-AI-Pentest Framework supporting multiple platforms and deployment scenarios.

## 📋 Table of Contents

- [Overview](#overview)
- [Supported Platforms](#supported-platforms)
- [Quick Start](#quick-start)
- [Template Documentation](#template-documentation)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

These templates provide seamless integration of security scanning into your CI/CD pipelines, enabling:

- **Automated Security Scans** on every commit, PR, or scheduled basis
- **Multi-Platform Support** for GitHub Actions, GitLab CI, Jenkins, Azure DevOps, and Kubernetes
- **Comprehensive Reporting** with SARIF, HTML, JSON, and PDF formats
- **Compliance Checking** against OWASP Top 10, PCI DSS, ISO 27001
- **Notifications** via Slack, Discord, Email, Teams
- **Issue/Ticket Creation** for tracking vulnerabilities

## 🏢 Supported Platforms

| Platform | File | Status | Features |
|----------|------|--------|----------|
| GitHub Actions | `github-actions-template.yml` | ✅ Production-Ready | Full featured with SARIF upload |
| GitLab CI | `gitlab-ci-template.yml` | ✅ Production-Ready | Security Dashboard integration |
| Jenkins | `Jenkinsfile` | ✅ Production-Ready | HTML Publisher, JIRA integration |
| Azure DevOps | `azure-pipelines.yml` | ✅ Production-Ready | Work Items, Test Results |
| Kubernetes | `../k8s/zen-pentest-crd.yaml` | ✅ Production-Ready | Operator, CRD, CronJobs |
| Docker Compose | `../docker/docker-compose.ci.yml` | ✅ Production-Ready | Full stack with DB & Cache |

## 🚀 Quick Start

### GitHub Actions

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Weekly

jobs:
  security:
    uses: your-org/zen-ai-pentest/.github/workflows/github-actions-template.yml@main
    with:
      target: 'https://your-app.com'
      scan_mode: 'full'
    secrets:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
include:
  - remote: 'https://raw.githubusercontent.com/your-org/zen-ai-pentest/main/ci_cd/gitlab-ci-template.yml'

variables:
  ZEN_SCAN_TARGET: "https://your-app.com"
  ZEN_SCAN_MODE: "full"
```

### Jenkins

```groovy
// Jenkinsfile
@Library('zen-pentest') _

zenPentestScan(
    target: 'https://your-app.com',
    scanMode: 'full',
    intensity: 'medium',
    createJiraTickets: true
)
```

### Kubernetes

```bash
# Install the operator
kubectl apply -f https://raw.githubusercontent.com/your-org/zen-ai-pentest/main/k8s/zen-pentest-crd.yaml

# Create a scan
kubectl apply -f - <<EOF
apiVersion: security.zen.io/v1
kind: ZenPentestScan
metadata:
  name: production-scan
  namespace: zen-security
spec:
  target: "https://your-app.com"
  scanMode: full
  schedule: "0 2 * * 0"
EOF
```

### Docker Compose

```bash
# Clone repository
git clone https://github.com/your-org/zen-ai-pentest.git
cd zen-ai-pentest

# Create environment file
cat > .env <<EOF
ZEN_SCAN_TARGET=https://your-app.com
ZEN_SCAN_MODE=full
OPENAI_API_KEY=sk-your-key
EOF

# Run scan
docker-compose -f docker/docker-compose.ci.yml up --exit-code-from zen-pentest
```

## 📖 Template Documentation

### GitHub Actions Template

**Features:**
- Multiple trigger types (push, PR, schedule, manual)
- Configurable scan modes (recon, vuln, full, stealth)
- Automatic SARIF upload to GitHub Security tab
- Artifact upload and retention
- Job summary with Markdown report
- GitHub issue creation for critical findings
- Slack/Discord notifications
- Compliance gate with configurable thresholds

**Required Secrets:**
- `OPENAI_API_KEY` - OpenAI API key for AI analysis
- `SLACK_WEBHOOK_URL` - Slack webhook URL (optional)
- `DISCORD_WEBHOOK_URL` - Discord webhook URL (optional)

**Environment Variables:**
- `ZEN_PENTEST_DEFAULT_TARGET` - Default target URL
- `ZEN_PENTEST_MAX_CRITICAL` - Max allowed critical vulnerabilities (default: 0)
- `ZEN_PENTEST_MAX_HIGH` - Max allowed high vulnerabilities (default: 5)
- `ZEN_PENTEST_MAX_RISK_SCORE` - Max allowed risk score (default: 50)

### GitLab CI Template

**Features:**
- Multiple stages (build, test, security, report, notify)
- Docker service integration
- Cache configuration for faster builds
- Security Dashboard integration via SARIF
- Merge Request discussions
- GitLab issues creation
- Scheduled pipeline support

**Required Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `GITLAB_API_TOKEN` - API token for issue creation
- `SLACK_WEBHOOK_URL` - Slack webhook (optional)

### Jenkins Pipeline

**Features:**
- Declarative pipeline with Docker agent
- Parameterized builds
- HTML report publishing
- JIRA ticket creation
- Email notifications
- Extensive error handling
- Build status tracking

**Required Plugins:**
- Pipeline
- Docker Pipeline
- HTML Publisher
- JUnit
- Email Extension
- JIRA (optional)

**Parameters:**
- `TARGET` - Target URL/IP
- `SCAN_MODE` - Scan mode (full, recon, vuln, stealth)
- `INTENSITY` - Scan intensity (low, medium, high)
- `CREATE_JIRA_TICKETS` - Create JIRA tickets for findings
- `EMAIL_NOTIFICATION` - Send email notifications
- `FAIL_ON_THRESHOLD` - Fail build on threshold violation

### Azure DevOps Pipeline

**Features:**
- Container jobs for isolation
- Service connections for secrets
- Test results integration
- Work item creation
- Pipeline artifacts
- Microsoft Teams notifications
- Compliance gates

**Required Service Connections:**
- `docker-hub-connection` - Docker Hub connection
- Variable groups for secrets

**Variable Groups:**
- `zen-pentest-secrets` - API keys, tokens
- `zen-pentest-config` - Configuration values

### Kubernetes CRD

**Features:**
- Custom Resource Definition for ZenPentestScan
- Scheduled scans (CronJob-like)
- ConfigMap for configuration
- Secret management for API keys
- Persistent Volume Claims for reports
- ServiceMonitor for Prometheus metrics
- Network policies for security
- RBAC configuration

**Resources:**
- Namespace: `zen-security`
- CRD: `zenpentestscans.security.zen.io`
- Operator: `zen-pentest-operator`
- ConfigMap: `zen-pentest-config`
- Secret: `zen-pentest-secrets`

### Docker Compose CI

**Services:**
- `zen-pentest` - Main scanning service
- `postgres` - Database for scan results
- `redis` - Caching and queue management
- `minio` - S3-compatible storage (optional)
- `report-viewer` - Web UI for reports (optional)
- `scheduler` - Cron-like scheduler (optional)

**Profiles:**
- Default: Core scanning functionality
- `with-storage`: Includes MinIO
- `with-ui`: Includes report viewer
- `with-scheduler`: Includes scan scheduler

## 🔒 Security Best Practices

### Secret Management

1. **Never commit secrets to version control**
   ```bash
   # Use environment variables or secret managers
   export OPENAI_API_KEY=$(aws secretsmanager get-secret-value ...)
   ```

2. **Use platform-specific secret storage:**
   - GitHub: Repository/Organization Secrets
   - GitLab: CI/CD Variables (Masked & Protected)
   - Jenkins: Credentials Plugin
   - Azure DevOps: Variable Groups with secret variables
   - Kubernetes: Sealed Secrets or External Secrets Operator

3. **Rotate API keys regularly**

### Network Security

1. **Use private networks when possible**
   ```yaml
   networks:
     zen-network:
       internal: true  # No external access
   ```

2. **Bind services to localhost only**
   ```yaml
   ports:
     - "127.0.0.1:5432:5432"
   ```

3. **Implement NetworkPolicies in Kubernetes**

### Scan Safety

1. **Use appropriate scan intensity for environment:**
   - Production: `stealth` or `low`
   - Staging: `medium`
   - Development: `high`

2. **Always get proper authorization before scanning**

3. **Respect rate limits and scanning windows**

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `ZEN_SCAN_TARGET` | Target URL/IP | - | Yes |
| `ZEN_SCAN_MODE` | Scan mode | `full` | No |
| `ZEN_SCAN_INTENSITY` | Scan intensity | `medium` | No |
| `SLACK_WEBHOOK_URL` | Slack webhook | - | No |
| `POSTGRES_PASSWORD` | PostgreSQL password | `zenpass` | No |
| `REDIS_PASSWORD` | Redis password | `redispass` | No |

### Scan Modes

| Mode | Description | Duration | Use Case |
|------|-------------|----------|----------|
| `recon` | Reconnaissance only | ~5-10 min | Initial discovery |
| `vuln` | Vulnerability scan | ~30-60 min | Regular CI/CD |
| `full` | Full assessment | ~1-3 hours | Comprehensive |
| `stealth` | Low and slow | ~2-8 hours | Production |

### Compliance Standards

- **OWASP Top 10** - Web application security
- **PCI DSS** - Payment card industry
- **ISO 27001** - Information security management
- **NIST CSF** - Cybersecurity framework
- **SOC 2** - Service organization controls

## 🐛 Troubleshooting

### Common Issues

**Issue: OpenAI API rate limit exceeded**
```
Solution: Reduce scan intensity or implement exponential backoff
```

**Issue: Target unreachable**
```
Solution: Check network connectivity and firewall rules
```

**Issue: Permission denied in Kubernetes**
```
Solution: Verify RBAC configuration and service account permissions
```

**Issue: Out of memory**
```
Solution: Increase memory limits in resource configuration
```

### Debug Mode

Enable debug logging:
```yaml
env:
  ZEN_LOG_LEVEL: DEBUG
  ZEN_VERBOSE: true
```

### Getting Help

- 📚 Documentation: https://docs.zen-pentest.io
- 💬 Discord: https://discord.gg/zen-pentest
- 🐛 Issues: https://github.com/zenai/pentest/issues
- 📧 Email: support@zen-pentest.io

## 📄 License

These templates are released under the MIT License. See [LICENSE](../LICENSE) for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

<p align="center">
  Made with ❤️ by the Zen-AI-Pentest Team
</p>
