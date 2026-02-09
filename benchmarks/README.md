# Zen-AI-Pentest Benchmarking & Testing Framework

Ein umfassendes Benchmarking-Framework zur Bewertung der Performance, Genauigkeit und Effizienz des Zen-AI-Pentest Frameworks im Vergleich zu anderen Sicherheitstools.

## Features

- **📊 Umfassende Metrik-Erfassung**: Precision, Recall, F1-Score, Coverage, Performance
- **🎯 Test-Szenarien**: OWASP Juice Shop, DVWA, Metasploitable, WebGoat, HTB, THM
- **⚖️ Tool-Vergleiche**: PentestGPT, AutoPentest-DRL, Nessus, OpenVAS, Burp Suite, etc.
- **🔍 Regressions-Erkennung**: Automatische Erkennung von Performance-Regessionen
- **📈 Trend-Analyse**: Historische Performance-Tracking
- **🤖 CI/CD Integration**: GitHub Actions, GitLab CI, Jenkins
- **📊 Visualisierung**: Charts, Reports, Dashboards

## Installation

```bash
# Requirements installieren
pip install -r benchmarks/requirements.txt

# Oder einzelne Pakete
pip install rich matplotlib aiohttp
```

## Schnellstart

### Verfügbare Szenarien auflisten

```bash
python -m benchmarks.run_benchmarks list

# Mit Filter
python -m benchmarks.run_benchmarks list --difficulty easy
python -m benchmarks.run_benchmarks list --type web_app
python -m benchmarks.run_benchmarks list --tag owasp
```

### Benchmark ausführen

```bash
# Einzelne Szenarien
python -m benchmarks.run_benchmarks run --scenarios dvwa juice-shop

# Alle Szenarien
python -m benchmarks.run_benchmarks run --all

# Nach Schwierigkeitsgrad
python -m benchmarks.run_benchmarks run --difficulty easy

# Mit Name und paralleler Ausführung
python -m benchmarks.run_benchmarks run \
    --scenarios dvwa juice-shop webgoat \
    --name "my-benchmark" \
    --concurrent 2 \
    --timeout 1800

# Mit Tool-Vergleich
python -m benchmarks.run_benchmarks run \
    --scenarios dvwa \
    --compare \
    --competitors "PentestGPT" "Nuclei"
```

### Ergebnisse anzeigen

```bash
# Report anzeigen
python -m benchmarks.run_benchmarks view <benchmark-id>

# Historie anzeigen
python -m benchmarks.run_benchmarks history --limit 20

# Zwei Reports vergleichen
python -m benchmarks.run_benchmarks compare <id1> <id2>
```

### Visualisierung

```bash
# Chart für einzelnen Benchmark
python -m benchmarks.run_benchmarks chart --benchmark <benchmark-id>

# Trend-Chart über alle Benchmarks
python -m benchmarks.run_benchmarks chart
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Benchmark

on:
  pull_request:
    branches: [ main ]
  push:
    tags: [ 'v*' ]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Quick Benchmark
        run: python -m benchmarks.run_benchmarks ci --type quick
        
      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: benchmark_results/
```

### Lokale CI-Ausführung

```bash
# Quick Benchmark (für PRs)
python -m benchmarks.run_benchmarks ci --type quick

# Full Benchmark (für Releases)
python -m benchmarks.run_benchmarks ci --type full

# Mit Fehler bei Regessionen
python -m benchmarks.run_benchmarks ci \
    --type quick \
    --fail-on-gate \
    --fail-on-regression
```

## API Verwendung

### Einfacher Benchmark

```python
import asyncio
from benchmarks import BenchmarkEngine, BenchmarkConfig

async def run_benchmark():
    engine = BenchmarkEngine()
    
    config = BenchmarkConfig(
        benchmark_name="my-test",
        scenarios=["dvwa", "juice-shop"],
        max_concurrent=2
    )
    
    report = await engine.run_benchmark(config)
    
    print(f"Success Rate: {report.success_rate:.1f}%")
    print(f"Duration: {report.duration_seconds:.1f}s")
    
    # Aggregate Metriken
    if report.aggregate_metrics:
        print(f"Avg F1-Score: {report.aggregate_metrics['avg_f1_score']:.3f}")

asyncio.run(run_benchmark())
```

### Erweiterte Metriken

```python
from benchmarks import (
    BenchmarkMetrics,
    ClassificationMetrics,
    CoverageMetrics
)

# Metriken erstellen
metrics = BenchmarkMetrics(
    benchmark_id="test-123",
    scenario_name="DVWA",
    tool_version="1.0.0"
)

# Classification Metriken
metrics.classification = ClassificationMetrics(
    true_positives=42,
    false_positives=3,
    true_negatives=95,
    false_negatives=5
)

print(f"Precision: {metrics.classification.precision:.3f}")
print(f"Recall: {metrics.classification.recall:.3f}")
print(f"F1-Score: {metrics.classification.f1_score:.3f}")

# Aggregate Scores
scores = metrics.calculate_aggregate_scores()
print(f"Overall Score: {scores['overall']:.3f}")
```

### Tool-Vergleich

```python
from benchmarks.comparison import ComparisonFramework

framework = ComparisonFramework()

# Verfügbare Konkurrenten anzeigen
available = framework.get_available_competitors()
print(f"Available: {available}")

# Vergleich durchführen
comparison = await framework.run_comparison(
    zen_result=zen_benchmark_result,
    scenario_config={"target_url": "http://localhost:8080"},
    competitors=["Nuclei", "OWASP ZAP"]
)

# Markdown Report
print(comparison.generate_report_markdown())
```

## Metriken

### Classification Metrics

| Metrik | Beschreibung |
|--------|-------------|
| Precision | TP / (TP + FP) |
| Recall | TP / (TP + FN) |
| F1-Score | Harmonisches Mittel von Precision und Recall |
| Accuracy | (TP + TN) / Gesamt |
| Specificity | TN / (TN + FP) |
| Matthews Correlation | Korrelationskoeffizient (-1 bis +1) |

### Performance Metrics

| Metrik | Beschreibung |
|--------|-------------|
| MTTD | Mean Time to Detect |
| Scan Duration | Gesamtdauer des Scans |
| Memory Peak | Maximale Speichernutzung |
| CPU Usage | Durchschnittliche CPU-Auslastung |
| API Tokens | Verbrauchte API-Token |

### Coverage Metrics

| Metrik | Beschreibung |
|--------|-------------|
| Endpoint Coverage | % gescannter Endpunkte |
| Parameter Coverage | % getesteter Parameter |
| OWASP Coverage | % abgedeckter OWASP-Kategorien |
| Attack Vector Coverage | % getesteter Angriffsvektoren |

## Verfügbare Szenarien

### Training Applications

| Szenario | ID | Schwierigkeit | Vulnerabilities |
|----------|-----|--------------|-----------------|
| OWASP Juice Shop | `juice-shop` | Medium | 100+ |
| DVWA | `dvwa` | Easy | 10 |
| WebGoat | `webgoat` | Easy-Medium | 30+ |

### Vulnerable VMs

| Szenario | ID | Schwierigkeit | Services |
|----------|-----|--------------|----------|
| Metasploitable 2 | `metasploitable2` | Medium | 20+ |
| Metasploitable 3 | `metasploitable3` | Hard | 15+ |

### CTF Plattformen

| Szenario | ID | Plattform |
|----------|-----|-----------|
| HTB Starting Point | `htb-starting-point` | HackTheBox |
| HTB Web Challenges | `htb-web-challenges` | HackTheBox |
| THM OWASP Top 10 | `thm-owasp-top10` | TryHackMe |
| THM RootMe | `thm-rootme` | TryHackMe |

## Performance Gates

Standard-Performance-Gates für CI/CD:

```python
performance_gates = [
    PerformanceGate("precision_min", "precision", 0.70),
    PerformanceGate("recall_min", "recall", 0.65),
    PerformanceGate("f1_min", "f1_score", 0.67),
    PerformanceGate("accuracy_min", "accuracy", 0.75),
]
```

## Regressions-Erkennung

### Schweregrade

| Schweregrad | Threshold | Aktion |
|------------|-----------|--------|
| Critical | < -30% | Build fail |
| High | < -20% | Warning |
| Medium | < -10% | Notice |
| Low | < -5% | Info |

## Output Formate

### JSON Report

```json
{
  "benchmark_id": "abc123",
  "benchmark_name": "my-test",
  "success_rate": 95.0,
  "aggregate_metrics": {
    "avg_precision": 0.85,
    "avg_recall": 0.82,
    "avg_f1_score": 0.83,
    "avg_accuracy": 0.88
  },
  "scenario_results": [...]
}
```

### JUnit XML

```xml
<testsuites>
  <testsuite name="Zen-AI-Pentest Benchmark" tests="5" failures="0">
    <testcase name="dvwa" time="120.5">
      <system-out>{"precision": 0.85, "recall": 0.82}</system-out>
    </testcase>
  </testsuite>
</testsuites>
```

## Konfiguration

### Umgebungsvariablen

```bash
# Output Verzeichnis
export ZEN_BENCHMARK_OUTPUT="benchmark_results"

# Parallelisierung
export ZEN_BENCHMARK_MAX_CONCURRENT=2

# Timeouts
export ZEN_BENCHMARK_TIMEOUT=3600

# Docker
export ZEN_BENCHMARK_USE_DOCKER=true
```

### Config File

```yaml
# benchmark_config.yaml
benchmark:
  name: "production-test"
  max_concurrent: 2
  timeout_per_scenario: 1800

scenarios:
  include:
    - dvwa
    - juice-shop
    - webgoat
  exclude:
    - metasploitable3

performance_gates:
  precision:
    min: 0.70
  recall:
    min: 0.65
  f1_score:
    min: 0.67

comparison:
  enabled: true
  competitors:
    - Nuclei
    - OWASP ZAP
```

## Entwicklung

### Tests ausführen

```bash
# Unit Tests
python -m pytest benchmarks/tests/

# Integration Tests
python -m pytest benchmarks/tests/integration/
```

### Neue Szenarien hinzufügen

```python
from benchmarks.scenarios import TestScenario, VulnerabilityProfile

MY_SCENARIO = TestScenario(
    id="my-app",
    name="My Vulnerable App",
    description="Custom vulnerable application",
    scenario_type=ScenarioType.WEB_APP,
    difficulty=DifficultyLevel.MEDIUM,
    target_url="http://localhost:8080",
    expected_vulnerabilities=[
        VulnerabilityProfile(
            vuln_type="sql_injection",
            severity="critical",
            location="/login",
            cwe_id="CWE-89"
        )
    ]
)
```

## Troubleshooting

### Docker-Szenarien starten nicht

```bash
# Docker Compose prüfen
docker-compose --version

# Container manuell starten
docker-compose -f benchmarks/docker/juice-shop.yml up -d
```

### Timeouts bei langen Scans

```bash
# Timeout erhöhen
python -m benchmarks.run_benchmarks run \
    --scenarios metasploitable3 \
    --timeout 7200
```

### Speicherprobleme

```bash
# Parallelisierung reduzieren
python -m benchmarks.run_benchmarks run \
    --all \
    --concurrent 1
```

## Lizenz

MIT License - Siehe [LICENSE](../LICENSE)

## Contributing

1. Fork erstellen
2. Feature-Branch: `git checkout -b feature/my-feature`
3. Änderungen committen: `git commit -am 'Add feature'`
4. Pushen: `git push origin feature/my-feature`
5. Pull Request erstellen

## Support

- Issues: [GitHub Issues](https://github.com/yourorg/zen-ai-pentest/issues)
- Dokumentation: [Wiki](https://github.com/yourorg/zen-ai-pentest/wiki)
- Discord: [Join Server](https://discord.gg/zen-ai-pentest)
