# Monitoring & Alerting Setup

Dieses Verzeichnis enthält die Monitoring- und Alerting-Konfiguration für Zen AI Pentest.

## Komponenten

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Prometheus │────▶│   Grafana   │◀────│ Alertmanager│
│  (Metrics)   │     │(Dashboards) │     │  (Alerts)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐                         ┌─────────────┐
│  Application │                         │ Slack/Discord│
│  (Scraper)   │                         │  (Notify)   │
└─────────────┘                         └─────────────┘
```

## Quick Start

### 1. Webhook URLs konfigurieren

```bash
# .env Datei erstellen
cat > .env << 'EOF'
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
SLACK_SECURITY_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SECURITY/WEBHOOK

# Grafana Zugangsdaten
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure-password

# Datenbank
DB_USER=postgres
DB_PASSWORD=secure-password
DB_NAME=zen_pentest
EOF
```

### 2. Monitoring Stack starten

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Zugriff

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin/admin |
| Alertmanager | http://localhost:9093 | - |

## Metriken

### HTTP Metriken

| Metrik | Beschreibung |
|--------|--------------|
| `http_requests_total` | Gesamtzahl der HTTP Requests |
| `http_request_duration_seconds` | Request Latenz (Histogram) |
| `http_requests_in_progress` | Aktive Requests |
| `http_errors_total` | HTTP Fehler |

### Business Metriken

| Metrik | Beschreibung |
|--------|--------------|
| `scans_created_total` | Erstellte Scans |
| `scans_completed_total` | Abgeschlossene Scans |
| `scans_active` | Aktive Scans |
| `findings_discovered_total` | Gefundene Vulnerabilities |
| `reports_generated_total` | Generierte Reports |

### Security Metriken

| Metrik | Beschreibung |
|--------|--------------|
| `auth_attempts_total` | Login Versuche |
| `active_sessions` | Aktive Sessions |
| `rate_limit_hits_total` | Rate Limit Überschreitungen |

### Datenbank Metriken

| Metrik | Beschreibung |
|--------|--------------|
| `db_connections_active` | Aktive DB Connections |
| `db_query_duration_seconds` | Query Latenz |

## Alerts

### Kritische Alerts

| Alert | Bedingung | Aktion |
|-------|-----------|--------|
| `HighErrorRate` | > 5% Fehlerrate | Slack + Discord |
| `AuthFailureSpike` | > 10% Auth-Failures | Slack + Discord |
| `ServiceDown` | API nicht erreichbar | Slack + Discord |
| `DiskSpaceLow` | < 10% Speicher | Slack + Discord |

### Warning Alerts

| Alert | Bedingung | Aktion |
|-------|-----------|--------|
| `HighLatency` | P95 > 2s | Slack |
| `DBConnectionsHigh` | > 25 Connections | Slack |
| `ScansStuck` | 30min keine Änderung | Slack |
| `HighMemoryUsage` | > 90% RAM | Slack |

### Info Alerts

| Alert | Bedingung | Aktion |
|-------|-----------|--------|
| `CriticalFinding` | Critical Vulnerability | Slack #security |
| `RateLimitThreshold` | > 10 hits/sec | Slack |

## Integration in FastAPI

### Metrics Middleware

```python
from fastapi import FastAPI
from monitoring.metrics import MetricsMiddleware, init_app_info

app = FastAPI()

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Initialize app info
init_app_info(version="2.2.0", environment="production")

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    from monitoring.metrics import get_metrics
    return Response(get_metrics(), media_type=CONTENT_TYPE_LATEST)
```

### Business Metrics

```python
from monitoring.metrics import record_scan_created, record_finding

@app.post("/api/scans")
async def create_scan():
    scan = await create_scan_logic()
    record_scan_created(scan_type="web")
    return scan

@app.post("/api/findings")
async def report_finding():
    finding = await report_finding_logic()
    record_finding(severity="high", vulnerability_type="xss")
    return finding
```

### Notifications

```python
from monitoring.notifications import send_critical_finding, send_auth_failure

# Critical finding discovered
await send_critical_finding(
    target="example.com",
    vulnerability="SQL Injection",
    severity="Critical",
    scan_id="scan-123"
)

# Auth failure
await send_auth_failure(
    username="admin",
    ip_address="192.168.1.1",
    failure_count=5
)
```

## Dashboards

### Grafana Dashboard importieren

1. Grafana öffnen: http://localhost:3000
2. Login mit admin/admin
3. Navigation → Dashboards → Import
4. `monitoring/grafana-dashboard.json` hochladen

### Dashboard Panels

- **Request Rate**: Anfragen pro Sekunde
- **Error Rate**: Fehlerrate in %
- **P95 Latency**: 95. Perzentil Latenz
- **Active Sessions**: Aktive Benutzer
- **Scan Overview**: Aktive/Abgeschlossene Scans
- **Findings by Severity**: Vulnerabilities nach Schwere
- **Auth Success/Failure**: Login-Statistik
- **Database Connections**: DB Connection Pool

## Webhook einrichten

### Slack

1. Slack App erstellen: https://api.slack.com/apps
2. "Incoming Webhooks" aktivieren
3. Webhook URL kopieren
4. In `.env` einfügen: `SLACK_WEBHOOK_URL=...`

### Discord

1. Server-Einstellungen → Integrationen
2. "Webhook erstellen"
3. Webhook URL kopieren
4. In `.env` einfügen: `DISCORD_WEBHOOK_URL=...`

## Troubleshooting

### Prometheus zeigt keine Metriken

```bash
# Prometheus Targets prüfen
curl http://localhost:9090/api/v1/targets

# Manual scrape test
curl http://localhost:8000/metrics
```

### Alerts werden nicht gesendet

```bash
# Alertmanager Status prüfen
curl http://localhost:9093/api/v1/status

# Test Alert senden
curl -X POST http://localhost:9093/-/reload
```

### Grafana zeigt "No Data"

1. Datenquelle prüfen: Configuration → Data Sources
2. Prometheus URL: http://prometheus:9090
3. "Save & Test" klicken

## Weiterentwicklung

### Neue Metrik hinzufügen

```python
from prometheus_client import Counter

MY_METRIC = Counter(
    "my_metric_total",
    "Description",
    ["label1"],
    registry=METRICS_REGISTRY
)

# Verwenden
MY_METRIC.labels(label1="value").inc()
```

### Neuen Alert hinzufügen

In `monitoring/alerts.yml`:

```yaml
- alert: MyNewAlert
  expr: my_metric_total > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "My metric is high"
    description: "Value is {{ $value }}"
```

---

**Letztes Update**: 2026-02-04
