"""
Risk Engine für das Zen-AI-Pentest Framework.

Dieses Paket enthält das vollständige Multi-Faktor Risk Scoring System:

Module:
- cvss_calculator_full: CVSS 3.1 Calculator (Base, Temporal, Environmental)
- epss_client_full: EPSS Integration mit Caching
- business_impact_full: Business Impact Scoring
- multi_factor_scorer: Multi-Faktor Risk Scorer
- risk_report: Risk Report Generation

Usage:
    # CVSS Berechnung
    from risk_engine import calculate_cvss
    result = calculate_cvss(
        attack_vector="NETWORK",
        attack_complexity="LOW",
        privileges_required="NONE",
        scope="CHANGED",
        confidentiality="HIGH",
        integrity="HIGH",
        availability="HIGH"
    )
    print(f"CVSS: {result.base_score}")  # 10.0

    # EPSS Abfrage
    from risk_engine import EPSSClientFull
    client = EPSSClientFull()
    score = client.get_score("CVE-2024-1234")
    print(f"EPSS: {score.percentage:.1f}%")

    # Multi-Faktor Risk Scoring
    from risk_engine import MultiFactorRiskScorer
    scorer = MultiFactorRiskScorer()
    risk = scorer.calculate(
        finding_title="Critical SQL Injection",
        target="prod.example.com",
        cvss_score=9.8,
        epss_score=0.85,
        business_factors={
            "data_sensitivity": "PII",
            "system_criticality": "CRITICAL",
            "exposure": "INTERNET",
            "compliance": ["GDPR"],
            "financial_impact": 1000000
        },
        validation_status="confirmed"
    )
    print(f"Risk: {risk.final_risk_score:.1f}/10")

    # Risk Report
    from risk_engine import RiskReport
    report = RiskReport(report_title="Security Assessment")
    report.add_finding_from_calculation(risk)
    print(report.to_markdown())
"""

# Legacy exports (backwards compatibility)
from .business_impact_calculator import (
    AssetContext,
    AssetCriticality,
    BusinessImpactCalculator,
    BusinessImpactResult,
    ComplianceFramework,
    ComplianceImpact,
    DataClassification,
    FinancialImpact,
    ReputationImpact,
    get_calculator,
)
from .business_impact_full import (
    BusinessImpactFactors,
    BusinessImpactScore,
    BusinessImpactScorer,
)
from .business_impact_full import ComplianceFramework as BusinessComplianceFramework
from .business_impact_full import (
    DataSensitivity,
    FinancialImpactEstimate,
    NetworkExposure,
    SystemCriticality,
    quick_business_score,
)
from .cvss import CVSSCalculator

# New Multi-Faktor Risk Scoring exports
from .cvss_calculator_full import (
    AttackComplexity,
    AttackVector,
    CVSS31Calculator,
    CVSSResult,
    ExploitCodeMaturity,
    ImpactLevel,
    PrivilegesRequired,
    RemediationLevel,
    ReportConfidence,
    Scope,
    SecurityRequirements,
    UserInteraction,
    calculate_cvss,
)
from .epss import EPSSClient
from .epss_client_full import (
    EPSSCache,
    EPSSClientFull,
    EPSSScore,
    get_epss_batch,
    get_epss_score,
)
from .false_positive_engine import (
    BayesianFilter,
    ConfidenceLevel,
    CVSSData,
    EPSSData,
    FalsePositiveDatabase,
    FalsePositiveEngine,
    Finding,
    FindingStatus,
    LLMVotingEngine,
    RiskFactors,
    ValidationResult,
    VulnerabilityType,
    create_finding_from_scan_result,
)
from .multi_factor_scorer import (
    MultiFactorRiskScore,
    MultiFactorRiskScorer,
    RiskComponent,
    RiskSeverity,
    calculate_risk,
)
from .risk_report import (
    ReportFormat,
    RiskFinding,
    RiskReport,
    RiskSummary,
    generate_quick_report,
)
from .scorer import RiskScore, RiskScorer, SeverityLevel

__all__ = [
    # Legacy
    "FalsePositiveEngine",
    "Finding",
    "ValidationResult",
    "RiskFactors",
    "CVSSData",
    "EPSSData",
    "ConfidenceLevel",
    "FindingStatus",
    "VulnerabilityType",
    "create_finding_from_scan_result",
    "FalsePositiveDatabase",
    "BayesianFilter",
    "LLMVotingEngine",
    "BusinessImpactCalculator",
    "BusinessImpactResult",
    "AssetContext",
    "AssetCriticality",
    "DataClassification",
    "ComplianceFramework",
    "FinancialImpact",
    "ComplianceImpact",
    "ReputationImpact",
    "get_calculator",
    "RiskScorer",
    "RiskScore",
    "SeverityLevel",
    "CVSSCalculator",
    "EPSSClient",
    # CVSS 3.1 Full
    "CVSS31Calculator",
    "CVSSResult",
    "AttackVector",
    "AttackComplexity",
    "PrivilegesRequired",
    "UserInteraction",
    "Scope",
    "ImpactLevel",
    "ExploitCodeMaturity",
    "RemediationLevel",
    "ReportConfidence",
    "SecurityRequirements",
    "calculate_cvss",
    # EPSS Full
    "EPSSClientFull",
    "EPSSCache",
    "EPSSScore",
    "get_epss_score",
    "get_epss_batch",
    # Business Impact Full
    "BusinessImpactScorer",
    "BusinessImpactScore",
    "BusinessImpactFactors",
    "FinancialImpactEstimate",
    "DataSensitivity",
    "SystemCriticality",
    "NetworkExposure",
    "BusinessComplianceFramework",
    "quick_business_score",
    # Multi-Faktor Risk Scorer
    "MultiFactorRiskScorer",
    "MultiFactorRiskScore",
    "RiskSeverity",
    "RiskComponent",
    "calculate_risk",
    # Risk Report
    "RiskReport",
    "RiskFinding",
    "RiskSummary",
    "ReportFormat",
    "generate_quick_report",
]

__version__ = "3.0.0"
