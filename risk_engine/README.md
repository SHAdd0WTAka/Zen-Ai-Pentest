# Risk Engine für Zen-AI-Pentest

Diese Risk Engine bietet fortschrittliche Funktionen zur **False-Positive-Reduzierung** und **Risk-Priorisierung** für Security-Findings.

## Features

### 1. Multi-Faktor-Validierung
- **CVSS v3.1 & v4.0** Scoring mit vollständiger Metrik-Unterstützung
- **EPSS** (Exploit Prediction Scoring System) Integration
- **Business Impact** Analyse
- **Kontext-Aware** Scoring

### 2. Multi-LLM-Voting
- Mehrere LLMs bewerten dasselbe Finding
- Konsens-basierte Entscheidung
- Confidence-Scoring basierend auf Einigkeit
- Disagreement-Resolution

### 3. Kontext-Faktoren
- Internet-facing vs. Internal
- Data Classification (PII, Financial, Health)
- Asset Criticality
- Exposure Surface
- Patch-Verfügbarkeit
- Exploit-Code Verfügbarkeit

### 4. Historische Validierung
- False-Positive-Datenbank mit Persistenz
- Bayesian-Filter für Text-Klassifizierung
- Lernen aus Benutzer-Feedback
- Ähnlichkeitssuche für wiederkehrende Findings

### 5. Business Impact Calculator
- Asset-Wertung und Klassifizierung
- Datenklassifizierung (Public, Internal, Confidential, Restricted)
- Compliance-Impact (PCI-DSS, HIPAA, GDPR, SOX, ISO27001, NIST)
- Reputation-Impact-Bewertung
- Financial-Impact-Berechnung

## Installation

```bash
# Die Risk Engine ist Teil des Zen-AI-Pentest Frameworks
# Keine zusätzliche Installation erforderlich
```

## Schnellstart

### False-Positive-Erkennung

```python
import asyncio
from risk_engine import FalsePositiveEngine, Finding, RiskFactors, CVSSData

async def main():
    # Engine initialisieren
    engine = FalsePositiveEngine(
        fp_database_path="fp_database.json",
        enable_llm_voting=True
    )

    # Finding erstellen
    finding = Finding(
        id="FIND-001",
        title="SQL Injection in Login",
        description="SQL Injection vulnerability detected...",
        severity="critical",
        risk_factors=RiskFactors(
            cvss_data=CVSSData(base_score=9.8),
            epss_score=0.95,
            business_impact=0.9,
            internet_exposed=True
        )
    )

    # Validieren
    result = await engine.validate_finding(finding)

    print(f"False Positive: {result.is_false_positive}")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Risk Score: {result.risk_score:.2f}")
    print(f"Priority: {result.priority}")

asyncio.run(main())
```

### Business Impact Berechnung

```python
from risk_engine import (
    BusinessImpactCalculator,
    AssetContext,
    AssetCriticality,
    DataClassification,
    ComplianceFramework
)

# Calculator initialisieren
calculator = BusinessImpactCalculator(
    organization_size="enterprise",
    annual_revenue=1000000000,
    industry="finance"
)

# Asset definieren
asset = AssetContext(
    asset_id="DB-001",
    asset_name="Customer Database",
    criticality=AssetCriticality.CRITICAL,
    data_classification=DataClassification.RESTRICTED,
    compliance_frameworks={ComplianceFramework.GDPR, ComplianceFramework.PCI_DSS},
    user_count=10000000,
    revenue_dependency=50.0
)

# Impact berechnen
impact = calculator.calculate_overall_impact(
    asset_context=asset,
    finding_type="sql_injection",
    severity="critical",
    breach_likelihood=0.8,
    data_volume_records=10000000
)

print(f"Gesamt-Score: {impact.overall_score:.2f}")
print(f"Finanzieller Impact: €{impact.financial_impact.total_costs:,.2f}")
print(f"Compliance-Risiko: {impact.compliance_impact.get_compliance_score():.2f}")
```

### Finding-Priorisierung

```python
from risk_engine import FalsePositiveEngine

engine = FalsePositiveEngine()

# Liste von Findings
findings = [finding1, finding2, finding3, ...]

# Priorisieren (höchste Priorität zuerst)
prioritized = engine.prioritize_findings(findings)

for finding in prioritized:
    print(f"{finding.id}: Priority {finding.status}")
```

## API-Referenz

### FalsePositiveEngine

#### `validate_finding(finding: Finding) -> ValidationResult`
Validiert ein einzelnes Finding und bestimmt FP-Status, Konfidenz und Priorität.

#### `multi_llm_voting(finding: Finding) -> Tuple[Dict[str, bool], float]`
Führt Multi-LLM-Voting durch und gibt die einzelnen Votes und Gesamtkonfidenz zurück.

#### `calculate_risk_score(factors: RiskFactors) -> float`
Berechnet einen Risiko-Score (0-1) basierend auf allen Faktoren.

#### `check_epss(cve_id: str) -> float`
Ruft den EPSS-Score für eine CVE-ID ab.

#### `prioritize_findings(findings: List[Finding]) -> List[Finding]`
Sortiert Findings nach Risikopriorität.

#### `learn_from_feedback(finding_id: str, is_fp: bool, user: Optional[str])`
Trainiert die Engine mit Benutzer-Feedback.

#### `register_llm(name: str, client: Any)`
Registriert einen LLM-Client für das Voting.

### BusinessImpactCalculator

#### `calculate_overall_impact(...) -> BusinessImpactResult`
Berechnet den gesamten Business Impact eines Findings.

#### `calculate_financial_impact(...) -> FinancialImpact`
Berechnet finanzielle Auswirkungen.

#### `calculate_compliance_impact(...) -> ComplianceImpact`
Bewertet Compliance-Auswirkungen.

#### `assess_reputation_impact(...) -> ReputationImpact`
Bewertet Reputationsrisiken.

## Konfiguration

### Environment Variables

```bash
# EPSS API Endpoint
EPSS_API_ENDPOINT=https://api.first.org/data/v1/epss

# FP Datenbank Pfad
FP_DATABASE_PATH=/var/lib/zen-ai/fp_database.json

# LLM Voting aktivieren/deaktivieren
ENABLE_LLM_VOTING=true
```

### Thresholds anpassen

```python
engine = FalsePositiveEngine()

# FP-Konfidenz-Threshold (default: 0.75)
engine.fp_confidence_threshold = 0.8

# Bestätigungs-Threshold (default: 0.85)
engine.confirmed_confidence_threshold = 0.9
```

## Risk-Score Berechnung

Der Risk-Score wird nach folgender Formel berechnet:

```
Risk = f(CVSS, EPSS, BusinessImpact, Exploitability, AssetValue)

Komponenten:
- CVSS (25%): Normalisierter CVSS-Score / 10
- EPSS (20%): Exploit-Wahrscheinlichkeit
- Business Impact (20%): Geschäftlicher Impact
- Exploitability (15%): Ausnutzbarkeit
- Context (20%): Kontext-Multiplikatoren

Multiplikatoren:
- Internet-exposed: +40%
- Exploit-Code verfügbar: +30%
- Aktive Ausnutzung beobachtet: +50%
- Kein Patch verfügbar: +20%
```

## Integration mit Zen-AI-Pentest Core

```python
from zen_ai_pentest.core import Scanner
from risk_engine import FalsePositiveEngine, create_finding_from_scan_result

# Scanner und Engine initialisieren
scanner = Scanner()
engine = FalsePositiveEngine()

# Scan durchführen
scan_results = await scanner.scan_target("https://example.com")

# In Findings umwandeln und validieren
findings = [create_finding_from_scan_result(r) for r in scan_results]
validation_results = await asyncio.gather(*[
    engine.validate_finding(f) for f in findings
])

# Nur echte Schwachstellen filtern
real_vulnerabilities = [
    r for r in validation_results if not r.is_false_positive
]
```

## LLM Integration

```python
# Eigenen LLM-Client registrieren
class MyLLMClient:
    async def analyze(self, prompt: str) -> str:
        # LLM-API-Aufruf
        response = await call_llm_api(prompt)
        return response

engine.register_llm("my_llm", MyLLMClient())
```

## Logging

Die Engine verwendet das Python `logging`-Modul:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_engine")
```

## Tests

```bash
# Beispiele ausführen
python risk_engine/example_usage.py
```

## Lizenz

MIT License - Teil des Zen-AI-Pentest Frameworks.
