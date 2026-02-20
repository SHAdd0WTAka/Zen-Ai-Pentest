# Health Check System

Comprehensive health monitoring system for Zen-AI-Pentest that checks database connectivity, security tool availability, API health, system resources, and security configuration.

## Features

- **Database Health**: Connection status, query performance, disk usage
- **Tool Availability**: Check if security tools are installed (nmap, nuclei, sqlmap, etc.)
- **API Health**: Backend API connectivity, response time, authentication status
- **Memory & Resources**: Memory usage, CPU usage, disk space
- **Security Checks**: SSL certificate validity, environment variables, secrets scanning

## Quick Start

### Run from CLI

```bash
# Run all health checks
python scripts/health_check_cli.py

# Run specific checks
python scripts/health_check_cli.py --check database --check tools

# Output as JSON for CI/CD
python scripts/health_check_cli.py --format json --ci

# Check API at specific URL
python scripts/health_check_cli.py --check api --api-url http://api.example.com:8000

# Quiet mode (for scripts)
python scripts/health_check_cli.py --format json --quiet
```

### Use in Python Code

```python
from core.health_check import (
    HealthCheckRunner,
    HealthCheckConfig,
    run_health_check,
    check_database,
    check_tools,
)

# Simple usage - run all checks
report = run_health_check()
print(f"Overall status: {report.overall_status}")

# Run with custom config
config = HealthCheckConfig(
    check_database=True,
    check_tools=True,
    required_tools=["nmap", "sqlmap"],
    check_api=True,
    api_base_url="http://localhost:8000",
    check_resources=True,
    check_security=True,
)
report = run_health_check(config=config)

# Check specific component
db_result = check_database()
print(f"Database: {db_result.status}")

tools_result = check_tools(required_tools=["nmap", "nuclei"])
print(f"Tools: {tools_result.status}")

# Get JSON output
json_report = run_health_check(config=config, json_output=True)
```

## CLI Reference

### Options

| Option | Description |
|--------|-------------|
| `--check, -c` | Specific check to run (database, tools, api, resources, security) |
| `--format, -f` | Output format: text, json, markdown, csv |
| `--verbose, -v` | Show verbose output |
| `--quiet, -q` | Suppress non-essential output |
| `--ci` | CI/CD mode (exit non-zero on issues, output JSON) |
| `--config` | Path to configuration file |
| `--database-url` | Database URL override |
| `--skip-database` | Skip database checks |
| `--skip-tools` | Skip tool checks |
| `--api-url` | API base URL |
| `--skip-api` | Skip API checks |
| `--skip-resources` | Skip resource checks |
| `--skip-security` | Skip security checks |
| `--timeout` | Timeout per check in seconds (default: 30) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed (OK) |
| 1 | Some checks failed (WARNING/ERROR/CRITICAL) |
| 2 | CLI error or exception |

## Configuration

### Configuration File

Create a JSON or YAML configuration file:

```json
{
  "check_database": true,
  "database_url": "sqlite:///./zen_pentest.db",
  "database_timeout": 5,
  "check_tools": true,
  "required_tools": ["nmap", "sqlmap", "nuclei"],
  "optional_tools": ["gobuster", "ffuf", "amass"],
  "check_api": true,
  "api_base_url": "http://localhost:8000",
  "api_timeout": 10,
  "check_resources": true,
  "memory_warning_threshold": 80.0,
  "memory_critical_threshold": 95.0,
  "check_security": true,
  "required_env_vars": ["KIMI_API_KEY"],
  "ssl_check_hosts": ["localhost:8000"]
}
```

Use the configuration file:

```bash
python scripts/health_check_cli.py --config health_config.json
```

### Environment Variables

The health check system respects these environment variables:

- `DATABASE_URL` - Database connection URL
- `KIMI_API_KEY` - Required API key (checked by security module)
- Various tool paths if set (e.g., `NMAP_PATH`, `SQLMAP_PATH`)

## Health Check Types

### Database Check

Checks database connectivity and performance:

```python
from core.health_check import DatabaseHealthCheck, HealthCheckConfig

config = HealthCheckConfig(check_database=True, database_timeout=5)
check = DatabaseHealthCheck(config)
result = await check.run()

# Result details:
# - connection: ok/error
# - type: postgresql/sqlite
# - query_performance: ok/slow
# - size_mb: Database size
```

### Tools Check

Verifies security tool installation:

```python
from core.health_check import ToolsHealthCheck, HealthCheckConfig

config = HealthCheckConfig(
    check_tools=True,
    required_tools=["nmap", "sqlmap"],
    optional_tools=["nuclei", "gobuster"],
)
check = ToolsHealthCheck(config)
result = await check.run()

# Result details:
# - required: {tool_name: {available, path, version}}
# - optional: {tool_name: {available, path, version}}
```

### API Check

Checks API health and response times:

```python
from core.health_check import APIHealthCheck, HealthCheckConfig

config = HealthCheckConfig(
    check_api=True,
    api_base_url="http://localhost:8000",
    api_timeout=10,
)
check = APIHealthCheck(config)
result = await check.run()

# Result details:
# - health_endpoint: {status, response_time_ms, status_code}
# - auth_status: ok/unauthorized/error
```

### Resources Check

Monitors system resources:

```python
from core.health_check import ResourcesHealthCheck, HealthCheckConfig

config = HealthCheckConfig(
    check_resources=True,
    memory_warning_threshold=80.0,
    memory_critical_threshold=95.0,
)
check = ResourcesHealthCheck(config)
result = await check.run()

# Result details:
# - memory: {total_gb, available_gb, used_gb, percent}
# - cpu: {percent, count, frequency_mhz}
# - disks: [{device, mountpoint, total_gb, used_gb, percent}]
```

### Security Check

Validates security configuration:

```python
from core.health_check import SecurityHealthCheck, HealthCheckConfig

config = HealthCheckConfig(
    check_security=True,
    required_env_vars=["KIMI_API_KEY"],
    ssl_check_hosts=["localhost:8000"],
    secrets_scan_paths=["core", "agents", "tools"],
)
check = SecurityHealthCheck(config)
result = await check.run()

# Result details:
# - env_vars: {var_name: True/False}
# - ssl_certs: [{host, status, days_until_expiry, expired}]
# - secrets_found: [{file, line, type, snippet}]
```

## Custom Health Checks

Create custom health checks by extending `BaseHealthCheck`:

```python
from core.health_check import BaseHealthCheck, HealthCheckConfig, HealthStatus, HealthCheckResult

class CustomHealthCheck(BaseHealthCheck):
    name = "custom"
    description = "My custom health check"
    
    async def run(self) -> HealthCheckResult:
        start_time = time.time()
        
        try:
            # Your check logic here
            result = await self._run_async(self._do_check)
            
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.OK,
                "Custom check passed",
                result,
                duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return self._create_result(
                HealthStatus.ERROR,
                f"Custom check failed: {str(e)}",
                duration_ms=duration_ms
            )
    
    def _do_check(self):
        # Synchronous check logic
        return {"custom_data": "value"}

# Register and use
from core.health_check import HealthCheckRunner

HealthCheckRunner.CHECKS["custom"] = CustomHealthCheck
runner = HealthCheckRunner()
report = await runner.run_all_checks(["custom"])
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Health Check

on: [push, pull_request]

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run health checks
        run: python scripts/health_check_cli.py --ci
```

### GitLab CI

```yaml
health_check:
  stage: test
  script:
    - pip install -r requirements.txt
    - python scripts/health_check_cli.py --ci
  allow_failure: true
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python scripts/health_check_cli.py --check api --format json --quiet || exit 1
```

## API Integration

The health check system can be integrated with the Zen-AI-Pentest API:

```python
from fastapi import FastAPI
from core.health_check import HealthCheckRunner, HealthCheckConfig

app = FastAPI()

@app.get("/health")
async def health_check():
    config = HealthCheckConfig()
    runner = HealthCheckRunner(config)
    report = await runner.run_all_checks()
    return report.to_dict()

@app.get("/health/{check_name}")
async def specific_check(check_name: str):
    runner = HealthCheckRunner()
    result = runner.run_check(check_name)
    return result.to_dict()
```

## Monitoring Integration

### Prometheus

Export health metrics to Prometheus:

```python
from prometheus_client import Gauge, generate_latest

health_status = Gauge('zen_health_status', 'Health check status', ['check_name'])

async def update_metrics():
    runner = HealthCheckRunner()
    report = await runner.run_all_checks()
    
    for check in report.checks:
        status_value = {'ok': 0, 'warning': 1, 'error': 2, 'critical': 3, 'skipped': 4}
        health_status.labels(check_name=check.name).set(status_value[check.status.value])
```

## Troubleshooting

### Common Issues

**"Module not found" error**
```bash
pip install psutil pydantic
```

**"Permission denied" on Windows**
Run PowerShell/Command Prompt as Administrator.

**Tool not found**
Ensure tools are in PATH or set explicit paths in configuration.

**Database connection fails**
Check DATABASE_URL environment variable or pass --database-url option.

### Debug Mode

Enable verbose output for debugging:

```bash
python scripts/health_check_cli.py --verbose
```

Run specific check with debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from core.health_check import run_health_check
report = run_health_check()
```

## License

MIT License - See LICENSE file for details.
