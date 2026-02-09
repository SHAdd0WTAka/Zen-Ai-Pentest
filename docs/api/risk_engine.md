# Risk Engine API

## Risk Scorer

### Class: `RiskScorer`

Multi-factor risk scoring engine.

```python
from risk_engine import RiskScorer, RiskScore, SeverityLevel

scorer = RiskScorer(
    enable_epss=True,
    enable_business_context=True
)
```

#### Formula

```
Risk Score = (CVSS×0.25 + EPSS×0.25 + Business×0.35 + Validation×0.15) × 10
```

#### Methods

##### `calculate(finding: Dict, target_context: Optional[Dict] = None) -> RiskScore`

Calculate comprehensive risk score.

**Parameters:**
- `finding` (dict): Vulnerability finding with CVSS, CVE, etc.
- `target_context` (dict, optional): Target information

**Returns:**
- `RiskScore` object with all components

**Example:**
```python
score = scorer.calculate(
    finding={
        "cvss_score": 9.8,
        "cve_id": "CVE-2021-44228",
        "exploit_available": True
    },
    target_context={
        "internet_facing": True,
        "data_sensitivity": "pii",
        "compliance": ["gdpr"]
    }
)

print(f"Risk: {score.value}")  # 0-10
print(f"Severity: {score.severity}")  # SeverityLevel
print(f"SLA: {score.severity.sla}")  # 24h, 72h, 14d, 30d
```

##### `prioritize_findings(findings: List[Dict], target_context: Optional[Dict] = None) -> List[Dict]`

Sort findings by risk score.

### Class: `RiskScore`

Complete risk score with all components.

```python
@dataclass
class RiskScore:
    value: float  # 0-10
    severity: SeverityLevel
    cvss_score: float  # 0-1
    epss_score: float  # 0-1
    business_impact_score: float  # 0-1
    exploit_validation_score: float  # 0-1
    prioritized_actions: List[str]
```

### Enum: `SeverityLevel`

| Level | Range | SLA |
|-------|-------|-----|
| CRITICAL | 9.0-10.0 | 24h |
| HIGH | 7.0-8.9 | 72h |
| MEDIUM | 4.0-6.9 | 14d |
| LOW | 1.0-3.9 | 30d |
| INFO | 0.0-0.9 | Best effort |

## CVSS Calculator

### Class: `CVSSCalculator`

Calculate CVSS scores from various inputs.

```python
from risk_engine.cvss import CVSSCalculator

calc = CVSSCalculator()
score = calc.from_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
```

## EPSS Client

### Class: `EPSSClient`

Fetch EPSS scores from first.org API.

```python
from risk_engine.epss import EPSSClient

client = EPSSClient()
probability = client.get_score("CVE-2021-44228")
print(f"Exploit probability: {probability:.1%}")
```

## Business Impact Calculator

### Class: `BusinessImpactCalculator`

Calculate business impact based on context.

```python
from risk_engine.business_impact import BusinessImpactCalculator

calc = BusinessImpactCalculator()
impact = calc.calculate(
    finding={},
    context={
        "internet_facing": True,
        "data_sensitivity": "pii",
        "compliance": ["gdpr", "pci-dss"],
        "asset_criticality": "high"
    }
)
```
