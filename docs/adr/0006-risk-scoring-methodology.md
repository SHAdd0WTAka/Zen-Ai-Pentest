# ADR 0006: Risk Scoring Methodology

## Status
Proposed

## Context
CVSS alone is insufficient for prioritization. Need contextual risk assessment.

## Decision
Multi-factor risk scoring combining CVSS, EPSS, and business context.

## Formula

```python
def calculate_risk(finding: Finding) -> RiskScore:
    cvss_score = finding.cvss.base_score / 10  # Normalize to 0-1

    epss_score = get_epss(finding.cve_id)  # 0-1 probability

    business_impact = calculate_business_impact(
        internet_exposed=finding.target.internet_facing,
        data_classification=finding.target.data_sensitivity,
        compliance_scope=finding.target.compliance_requirements
    )

    exploit_validation = validate_exploit(finding)  # 0 or 1

    # Weighted combination
    risk = (
        cvss_score * 0.25 +
        epss_score * 0.25 +
        business_impact * 0.35 +
        exploit_validation * 0.15
    )

    return RiskScore(
        value=risk,
        severity=risk_to_severity(risk),
        components={
            'cvss': cvss_score,
            'epss': epss_score,
            'business': business_impact,
            'validated': exploit_validation
        }
    )
```

## Components

### 1. CVSS (25%)
Standard severity from NVD or calculated.

### 2. EPSS (25%)
Exploit Prediction Scoring System.
```python
async def get_epss(cve_id: str) -> float:
    url = f"https://api.first.org/data/v1/epss?cve={cve_id}"
    response = await http.get(url)
    return response.json()['data'][0]['epss']
```

### 3. Business Impact (35%)
Contextual factors:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Internet-facing | 0.4 | 1.0 if public, 0.3 if internal |
| Data sensitivity | 0.3 | 1.0=PII/PHI, 0.7=financial, 0.4=internal, 0.1=public |
| Compliance | 0.2 | Sum of applicable requirements (SOX, GDPR, etc.) |
| Asset criticality | 0.1 | Business-defined criticality score |

### 4. Exploit Validation (15%)
Confirmed exploitation:
- 1.0 = Successfully exploited by tool
- 0.5 = Exploit code available
- 0.2 = Theoretically exploitable
- 0.0 = No known exploit

## Prioritization Matrix

| Risk Score | Priority | SLA |
|------------|----------|-----|
| 9.0 - 10.0 | Critical | 24h |
| 7.0 - 8.9 | High | 72h |
| 4.0 - 6.9 | Medium | 14d |
| 1.0 - 3.9 | Low | 30d |
| 0.0 - 0.9 | Info | Best effort |

## Implementation

```python
@dataclass
class RiskScore:
    value: float  # 0-10
    severity: Severity
    components: Dict[str, float]
    recommendations: List[str]
```

## Consequences

### Positive
- Better prioritization
- Context-aware decisions
- Aligns with business risk

### Negative
- Requires asset inventory
- Subjective weighting
- More complex calculation

## References
- [EPSS](https://www.first.org/epss/)
- [CVSS v3.1](https://www.first.org/cvss/specification-document)
- [FAIR Model](https://www.fairinstitute.org/)
