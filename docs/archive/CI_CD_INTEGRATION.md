# CI/CD Integration Guide

This guide covers integrating Zen AI Pentest into your CI/CD pipelines across multiple platforms.

## Table of Contents

- [Quick Start](#quick-start)
- [GitHub Actions](#github-actions)
- [GitLab CI/CD](#gitlab-cicd)
- [Jenkins](#jenkins)
- [Kubernetes](#kubernetes)
- [Output Formats](#output-formats)
- [Docker Usage](#docker-usage)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic Docker Usage

```bash
# Pull the image
docker pull zenai/zen-pentest:latest

# Run a quick scan
docker run -v $(pwd)/output:/app/output \
  zenai/zen-pentest:latest \
  scan https://example.com \
  --scope vuln \
  --format sarif \
  --output /app/output/results.sarif
```

### Using Docker Compose

```bash
# Set environment variables
export ZEN_TARGET=https://example.com
export ZEN_SCOPE=full
export ZEN_OUTPUT_FORMAT=sarif

# Run scan
docker-compose -f docker-compose.ci.yml run --rm scanner
```

## GitHub Actions

### Basic Usage

```yaml
- name: Run Security Scan
  uses: zen-ai-pentest/zen-ai-pentest@v2
  with:
    target: 'https://your-app.com'
    scope: 'full'
    fail-on: 'high'
    output-format: 'sarif'
```

### Full Example

```yaml
name: Security Scan

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * 0'  # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    permissions:
      security-events: write

    steps:
      - uses: actions/checkout@v4

      - name: Zen AI Pentest
        uses: ./
        with:
          target: 'https://staging.example.com'
          scope: 'full'
          fail-on: 'high'
          output-format: 'sarif'
          upload-sarif: 'true'
```

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `target` | Target URL or IP | Yes | - |
| `scope` | Scan scope | No | `full` |
| `fail-on` | Fail threshold | No | `high` |
| `output-format` | Output format | No | `sarif` |
| `intensity` | Scan intensity | No | `medium` |
| `modules` | Scan modules | No | `port_scan,web_scan,ssl_scan,ai_analysis` |
| `timeout` | Scan timeout | No | `3600` |
| `upload-sarif` | Upload to GitHub Security | No | `true` |

### Outputs

| Output | Description |
|--------|-------------|
| `scan-id` | Unique scan identifier |
| `results-file` | Path to results file |
| `findings-count` | Total findings |
| `critical-count` | Critical findings |
| `high-count` | High severity findings |
| `risk-score` | Risk score (0-100) |
| `scan-status` | Scan status |

## GitLab CI/CD

### Basic Template

Include the template in your `.gitlab-ci.yml`:

```yaml
include:
  - local: '.gitlab-ci-template.yml'

zen_security_scan:
  extends: .zen_pentest_scan
  variables:
    ZEN_TARGET: "https://your-app.com"
```

### Full Example

```yaml
stages:
  - test
  - security
  - deploy

include:
  - local: '.gitlab-ci-template.yml'

# Quick scan on merge requests
security:quick:
  extends: .zen_quick_scan
  stage: security
  variables:
    ZEN_TARGET: "https://staging.example.com"
  only:
    - merge_requests

# Full scan on main branch
security:full:
  extends: .zen_full_scan
  stage: security
  variables:
    ZEN_TARGET: "https://production.example.com"
  only:
    - main
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ZEN_TARGET` | Target URL | Required |
| `ZEN_SCOPE` | Scan scope | `full` |
| `ZEN_INTENSITY` | Scan intensity | `medium` |
| `ZEN_FAIL_ON` | Fail threshold | `high` |
| `ZEN_TIMEOUT` | Timeout (seconds) | `3600` |
| `ZEN_OUTPUT_FORMAT` | Output format | `sarif` |

### Security Dashboard Integration

GitLab automatically picks up SARIF files from artifacts:

```yaml
artifacts:
  reports:
    sast: zen-pentest-output/*.sarif
```

## Jenkins

### Basic Pipeline

Create a `Jenkinsfile`:

```groovy
pipeline {
    agent {
        docker {
            image 'zenai/zen-pentest:latest'
        }
    }

    environment {
        ZEN_TARGET = 'https://example.com'
        ZEN_SCOPE = 'full'
        ZEN_FAIL_ON = 'high'
    }

    stages {
        stage('Security Scan') {
            steps {
                sh '''
                    python -m zen_ai_pentest scan "$ZEN_TARGET" \
                        --scope $ZEN_SCOPE \
                        --format sarif \
                        --output results.sarif
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results.sarif'
        }
    }
}
```

### Advanced Pipeline

See `jenkins/Jenkinsfile.example` for a complete example with:
- Quality gates
- Notifications
- Multi-environment scanning
- Parallel scans

### Jenkins Plugins

Recommended plugins:
- **Warnings Next Generation**: For SARIF visualization
- **JUnit**: For test result parsing
- **HTML Publisher**: For HTML reports

## Kubernetes

### Operator Installation

```bash
# Install CRD and operator
kubectl apply -f k8s/operator/zenscan-crd.yaml
kubectl apply -f k8s/operator/operator-deployment.yaml

# Verify installation
kubectl get pods -n zen-operator
```

### Creating Scans

```bash
# Apply example scans
kubectl apply -f k8s/operator/example-zenscan.yaml

# Check status
kubectl get zenscans -n zen-security

# View results
kubectl logs -l job-name=zen-scan-<scan-name> -n zen-security
```

### Custom Resource Example

```yaml
apiVersion: security.zen.io/v1
kind: ZenScan
metadata:
  name: production-scan
  namespace: zen-security
spec:
  target: "https://production.example.com"
  scanMode: full
  intensity: medium
  output:
    formats:
      - sarif
      - html
  ciConfig:
    failOn: high
```

## Output Formats

### SARIF (GitHub/GitLab)

```python
from modules.output_formats import SARIFFormatter, Finding, ScanSummary

formatter = SARIFFormatter()
sarif_data = formatter.format(findings, summary)
formatter.write(findings, summary, "results.sarif")
```

Upload to GitHub:
```bash
gh api repos/owner/repo/code-scanning/sarifs \
  -F commit_sha=$GITHUB_SHA \
  -F ref=$GITHUB_REF \
  -F sarif=@results.sarif
```

### JUnit XML (Jenkins)

```python
from modules.output_formats import JUnitXMLFormatter

formatter = JUnitXMLFormatter()
xml_element = formatter.format(findings, summary)
formatter.write(findings, summary, "results.xml")
```

### HTML Reports

```python
from modules.output_formats import HTMLFormatter

formatter = HTMLFormatter()
formatter.write(findings, summary, "report.html")
```

### All Formats

```python
from modules.output_formats import export_all_formats

results = export_all_formats(
    findings,
    summary,
    output_dir="./output",
    prefix="security-scan"
)
# Returns: {'sarif': Path, 'junit': Path, 'html': Path, 'json': Path}
```

## Docker Usage

### Image Variants

| Variant | Size | Use Case |
|---------|------|----------|
| `latest` (~150MB) | Standard | Production scans |
| `ci` (~250MB) | CI optimized | GitHub/GitLab CI |
| `slim` (~80MB) | Minimal | Simple scans |
| `dev` (~300MB) | Development | Local development |

### Running Scans

```bash
# Basic scan
docker run --rm \
  -v $(pwd)/output:/app/output \
  zenai/zen-pentest:latest \
  scan https://example.com \
  --output /app/output/results.sarif

# With environment variables
docker run --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -v $(pwd)/output:/app/output \
  zenai/zen-pentest:latest \
  scan https://example.com

# CI mode with all outputs
docker run --rm \
  -e CI=true \
  -v $(pwd)/output:/app/output \
  zenai/zen-pentest:ci \
  scan https://example.com \
  --format all
```

### Docker Compose

```bash
# Start API server
docker-compose -f docker-compose.ci.yml up api

# Run scheduled scan
docker-compose -f docker-compose.ci.yml up scheduler

# Development environment
docker-compose -f docker-compose.ci.yml --profile dev up dev
```

## Troubleshooting

### Common Issues

#### Permission Denied

```bash
# Fix output directory permissions
chmod 777 ./output

# Or run with current user ID
docker run --user $(id -u):$(id -g) ...
```

#### Network Scanning Issues

```bash
# Add required capabilities
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN ...
```

#### GitHub SARIF Upload Fails

- Ensure `permissions: security-events: write` is set
- Check SARIF file size (< 1000 results recommended)
- Verify `upload-sarif: 'true'` is set

#### Large Scan Timeouts

```yaml
# Increase timeout in GitHub Actions
with:
  timeout: '7200'  # 2 hours

# Or in Docker
environment:
  - ZEN_TIMEOUT=7200
```

### Debug Mode

```bash
# Enable verbose output
python -m zen_ai_pentest scan ... --verbose

# Enable debug logging
docker run -e ZEN_DEBUG=true ...
```

### Getting Help

- GitHub Issues: https://github.com/zen-ai-pentest/zen-ai-pentest/issues
- Documentation: https://docs.zen-ai.dev
- Slack: #security-help

## Best Practices

1. **Scan Scope**: Use `vuln` for PR scans, `full` for scheduled scans
2. **Fail Thresholds**: Set `fail-on: high` for production pipelines
3. **Scheduling**: Run full scans weekly, quick scans on PRs
4. **Artifacts**: Retain SARIF files for compliance (90+ days)
5. **Notifications**: Configure Slack alerts for critical findings
6. **Baselines**: Establish risk score baselines and track trends

## License

MIT License - See LICENSE file for details.
